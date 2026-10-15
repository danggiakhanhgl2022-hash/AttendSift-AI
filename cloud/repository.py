"""Postgres durable state. No SQLite fallback, local mutex, or session advisory lock."""
from contextlib import contextmanager
from datetime import datetime
import hashlib
import uuid
from .retention import retention_cutoff


class LeaseBusy(ValueError):
    pass


class PostgresRepository:
    def __init__(self, url):
        if not url or not url.startswith(('postgres://', 'postgresql://')):
            raise ValueError('Cần DATABASE_URL PostgreSQL của Neon.')
        self.url = url

    @contextmanager
    def connection(self):
        import psycopg
        from psycopg.rows import dict_row
        with psycopg.connect(self.url, row_factory=dict_row, connect_timeout=10,
                             prepare_threshold=None) as conn:
            yield conn

    @staticmethod
    def json(value):
        from psycopg.types.json import Jsonb
        return Jsonb(value)

    def migrate(self):
        from pathlib import Path
        with self.connection() as conn:
            conn.execute(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))

    def get_setting(self, key, default=None):
        with self.connection() as conn:
            row = conn.execute('SELECT value FROM cc_settings WHERE key=%s', (key,)).fetchone()
            return row['value'] if row else default

    def set_setting(self, key, value):
        with self.connection() as conn:
            conn.execute('INSERT INTO cc_settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, self.json(value)))

    @contextmanager
    def lease(self, resource, seconds=180):
        owner = uuid.uuid4().hex
        with self.connection() as conn:
            row = conn.execute('''INSERT INTO cc_leases(resource,owner_token,expires_at)
                VALUES(%s,%s,now()+%s*interval '1 second') ON CONFLICT(resource)
                DO UPDATE SET owner_token=excluded.owner_token,expires_at=excluded.expires_at
                WHERE cc_leases.expires_at < now() RETURNING owner_token''', (resource, owner, seconds)).fetchone()
            if not row:
                raise LeaseBusy('Thao tác đang chạy; chờ rồi thử lại.')
        try:
            yield owner
        finally:
            with self.connection() as conn:
                conn.execute('DELETE FROM cc_leases WHERE resource=%s AND owner_token=%s', (resource, owner))

    def _assert_lease(self, conn, resource, owner):
        row = conn.execute('SELECT owner_token FROM cc_leases WHERE resource=%s AND owner_token=%s AND expires_at>now() FOR UPDATE', (resource, owner)).fetchone()
        if not row:
            raise LeaseBusy('Thao tác đã hết hạn; dữ liệu chưa được ghi. Hãy thử lại.')

    def save_messages(self, room, messages, owner):
        counts = {'added': 0, 'updated': 0, 'unchanged': 0, 'skipped_old': 0}
        cutoff = retention_cutoff()
        with self.connection() as conn:
            self._assert_lease(conn, 'sync:'+room, owner)
            for message in messages:
                if datetime.fromisoformat(message['send_time']) < cutoff:
                    counts['skipped_old'] += 1
                    continue
                digest = hashlib.sha256(message['body'].encode('utf-8')).hexdigest()
                old = conn.execute('SELECT body,content_hash,account_id,name,send_time FROM cc_messages WHERE room_id=%s AND message_id=%s FOR UPDATE', (room, message['message_id'])).fetchone()
                same_metadata=bool(old and old['account_id']==str(message.get('account_id') or '')
                    and old['name']==(message.get('name') or '')
                    and old['send_time']==datetime.fromisoformat(message['send_time']))
                if old and old['content_hash'] == digest and same_metadata:
                    counts['unchanged'] += 1
                    continue
                if old:
                    metadata={'account_id':old['account_id'],'name':old['name'],'send_time':old['send_time'].isoformat()}
                    conn.execute('INSERT INTO cc_message_versions(room_id,message_id,body,content_hash,metadata) VALUES(%s,%s,%s,%s,%s)', (room, message['message_id'], old['body'], old['content_hash'],self.json(metadata)))
                conn.execute('''INSERT INTO cc_messages(room_id,message_id,account_id,name,body,send_time,content_hash)
                    VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(room_id,message_id)
                    DO UPDATE SET account_id=excluded.account_id,name=excluded.name,body=excluded.body,
                    send_time=excluded.send_time,content_hash=excluded.content_hash,updated_at=now()''',
                    (room, message['message_id'], str(message.get('account_id') or ''), message.get('name') or '', message['body'], message['send_time'], digest))
                counts['updated' if old else 'added'] += 1
            conn.execute("INSERT INTO cc_settings(key,value) VALUES(%s,%s) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('last_sync:'+room, self.json(datetime.now().astimezone().isoformat())))
        return counts

    def purge_expired(self):
        """Delete expired business data atomically; retain configuration and keys."""
        cutoff = retention_cutoff()
        with self.connection() as conn:
            # Serialize with writers and lease acquisition for this short transaction.
            # A session already being processed is deferred until its lease expires.
            conn.execute("SET LOCAL lock_timeout = '5s'")
            conn.execute("""LOCK TABLE cc_leases, cc_sessions, cc_files,
                cc_actions, cc_messages, cc_message_versions IN SHARE ROW EXCLUSIVE MODE""")
            expired = """SELECT session_id FROM cc_sessions s
                WHERE s.created_at < %s AND NOT EXISTS (
                    SELECT 1 FROM cc_leases l WHERE l.resource='session:' || s.session_id
                    AND l.expires_at > now())"""
            counts = {}
            counts['files'] = conn.execute(
                'DELETE FROM cc_files WHERE session_id IN (' + expired + ')', (cutoff,)).rowcount
            counts['actions'] = conn.execute(
                'DELETE FROM cc_actions WHERE created_at < %s OR session_id IN (' + expired + ')',
                (cutoff, cutoff)).rowcount
            counts['sessions'] = conn.execute(
                'DELETE FROM cc_sessions WHERE session_id IN (' + expired + ')', (cutoff,)).rowcount
            counts['message_versions'] = conn.execute("""DELETE FROM cc_message_versions v
                WHERE v.version_time < %s OR EXISTS (
                    SELECT 1 FROM cc_messages m WHERE m.room_id=v.room_id
                    AND m.message_id=v.message_id AND m.send_time < %s)""",
                (cutoff, cutoff)).rowcount
            counts['messages'] = conn.execute(
                'DELETE FROM cc_messages WHERE send_time < %s', (cutoff,)).rowcount
        return {'cutoff': cutoff.isoformat(), 'deleted': counts}

    def messages(self, room, start, end):
        with self.connection() as conn:
            rows = conn.execute('SELECT message_id,room_id,account_id,name,body,send_time,content_hash FROM cc_messages WHERE room_id=%s AND send_time >= %s AND send_time < %s ORDER BY send_time,message_id', (room, start, end)).fetchall()
        for row in rows:
            row['send_time'] = row['send_time'].isoformat()
        return rows

    def create_session(self, value):
        with self.connection() as conn:
            row = conn.execute('''INSERT INTO cc_sessions(session_id,fingerprint,room_id,month,year,snapshot,ai_settings)
                VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(fingerprint) DO NOTHING RETURNING *''',
                (value['session_id'],value['fingerprint'],value['room_id'],value['month'],value['year'],self.json(value['snapshot']),self.json(value['ai_settings']))).fetchone()
            if not row:
                row = conn.execute('SELECT * FROM cc_sessions WHERE fingerprint=%s', (value['fingerprint'],)).fetchone()
            return row

    def session(self, sid):
        with self.connection() as conn:
            return conn.execute('SELECT * FROM cc_sessions WHERE session_id=%s', (sid,)).fetchone()

    def sessions(self):
        with self.connection() as conn:
            return conn.execute('SELECT session_id,month,year,status,error_message,created_at FROM cc_sessions ORDER BY created_at DESC LIMIT 100').fetchall()

    def save_analysis(self, sid, owner, *, raw_events, completed, results, status, error=None):
        with self.connection() as conn:
            self._assert_lease(conn, 'session:'+sid, owner)
            conn.execute('UPDATE cc_sessions SET raw_events=%s,completed=%s,results=%s,status=%s,error_message=%s,updated_at=now() WHERE session_id=%s', (self.json(raw_events),self.json(completed),self.json(results),status,error,sid))

    def save_file(self, sid, owner, filename, data):
        with self.connection() as conn:
            self._assert_lease(conn, 'session:'+sid, owner)
            conn.execute('INSERT INTO cc_files(session_id,filename,content,sha256) VALUES(%s,%s,%s,%s) ON CONFLICT(session_id) DO UPDATE SET filename=excluded.filename,content=excluded.content,sha256=excluded.sha256,created_at=now()', (sid, filename, data, hashlib.sha256(data).hexdigest()))
            conn.execute("UPDATE cc_sessions SET status='exported',updated_at=now() WHERE session_id=%s", (sid,))

    def file(self, sid):
        with self.connection() as conn:
            return conn.execute('SELECT filename,content,sha256 FROM cc_files WHERE session_id=%s', (sid,)).fetchone()

    def log(self, kind, status, summary, sid=None, details=None):
        with self.connection() as conn:
            conn.execute('INSERT INTO cc_actions(kind,status,summary,session_id,details) VALUES(%s,%s,%s,%s,%s)', (kind,status,summary,sid,self.json(details or {})))

    def history(self):
        with self.connection() as conn:
            return conn.execute('SELECT kind,status,summary,session_id,created_at FROM cc_actions ORDER BY id DESC LIMIT 100').fetchall()

    def login_allowed(self, fingerprint, limit=10):
        with self.connection() as conn:
            row = conn.execute('''INSERT INTO cc_login_attempts(fingerprint,attempts) VALUES(%s,1)
                ON CONFLICT(fingerprint) DO UPDATE SET
                attempts=CASE WHEN cc_login_attempts.window_start < now()-interval '15 minutes' THEN 1 ELSE cc_login_attempts.attempts+1 END,
                window_start=CASE WHEN cc_login_attempts.window_start < now()-interval '15 minutes' THEN now() ELSE cc_login_attempts.window_start END
                RETURNING attempts''', (fingerprint,)).fetchone()
            conn.execute("DELETE FROM cc_login_attempts WHERE window_start<now()-interval '1 day'")
            return row['attempts'] <= limit

    def create_auth_session(self, digest, lifetime_seconds):
        with self.connection() as conn:
            conn.execute('DELETE FROM cc_auth_sessions WHERE expires_at <= now()')
            conn.execute('INSERT INTO cc_auth_sessions(token_digest,expires_at) VALUES(%s,now()+%s*interval \'1 second\')', (digest,lifetime_seconds))

    def auth_session_valid(self, digest, idle_seconds):
        with self.connection() as conn:
            return conn.execute('''UPDATE cc_auth_sessions SET last_seen=now()
                WHERE token_digest=%s AND expires_at>now()
                AND last_seen>now()-%s*interval '1 second' RETURNING token_digest''',
                (digest,idle_seconds)).fetchone() is not None

    def revoke_auth_session(self, digest):
        with self.connection() as conn:
            conn.execute('DELETE FROM cc_auth_sessions WHERE token_digest=%s', (digest,))

    def ready(self):
        with self.connection() as conn:
            conn.execute('SELECT 1').fetchone()
            conn.execute('SELECT token_digest FROM cc_auth_sessions LIMIT 0')
        return True

    def error_summary(self):
        with self.connection() as conn:
            return conn.execute('''SELECT count(*) AS errors_24h, max(created_at) AS last_error_at
                FROM cc_actions WHERE status='failed' AND created_at>now()-interval '24 hours' ''').fetchone()
