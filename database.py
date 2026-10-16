# -*- coding: utf-8 -*-
"""
Database models and schema for ChamCongChatwork
"""
import sqlite3
import os
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import pytz

Vietnam_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

class ClosingConnection(sqlite3.Connection):
    """Commit or roll back, then release the file handle on context exit."""

    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


class Database:
    """SQLite database manager with migration support"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()
        from .migrations import migrate
        from ..utils.locking import FileMutex
        self.operation_lock = FileMutex(self.db_path + '.operation.lock')
        with self.operation_lock:
            migrate(self)

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, factory=ClosingConnection)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    account_id INTEGER,
                    name TEXT,
                    body TEXT NOT NULL,
                    send_time TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    is_deleted INTEGER DEFAULT 0
                )
            """)

            # Message versions for tracking edits
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_versions (
                    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    version_time TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    FOREIGN KEY (message_id) REFERENCES messages(message_id)
                )
            """)

            # Sync history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_history (
                    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_time TEXT NOT NULL,
                    source TEXT NOT NULL,
                    room_id TEXT,
                    status TEXT NOT NULL,
                    messages_new INTEGER DEFAULT 0,
                    messages_updated INTEGER DEFAULT 0,
                    messages_unchanged INTEGER DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Configuration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Export sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS export_sessions (
                    session_id TEXT PRIMARY KEY,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    ai_provider TEXT,
                    ai_model TEXT,
                    file_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # AI results (per session)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    employee_name TEXT,
                    display_name TEXT,
                    employee_code TEXT,
                    event_date TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_subtype TEXT,
                    reason TEXT,
                    hours_compensation TEXT,
                    is_compensated INTEGER DEFAULT 0,
                    minutes_not_compensated INTEGER DEFAULT 0,
                    minutes_compensated INTEGER DEFAULT 0,
                    leave_type TEXT,
                    is_excluded INTEGER DEFAULT 0,
                    source_message_ids TEXT,
                    confidence REAL,
                    needs_review INTEGER DEFAULT 0,
                    review_reason TEXT,
                    ai_raw_output TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES export_sessions(session_id)
                )
            """)

            # Corrections
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS corrections (
                    correction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    corrected_at TEXT NOT NULL,
                    correction_type TEXT,
                    FOREIGN KEY (result_id) REFERENCES ai_results(result_id)
                )
            """)

            # Action events (unified history)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_id TEXT NOT NULL,
                    session_id TEXT,
                    action_type TEXT NOT NULL,
                    action_time TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT,
                    details TEXT,
                    file_path TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_send_time ON messages(send_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_time ON sync_history(sync_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_export_month ON export_sessions(month, year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_results_session ON ai_results(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_action_time ON action_events(action_time)")

            conn.commit()

    def compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def now_vn(self) -> str:
        """Get current time in Vietnam timezone as ISO string"""
        return datetime.now(Vietnam_TZ).isoformat()


class MessageRepository:
    """Repository for message operations"""

    def __init__(self, db: Database):
        self.db = db

    def get_connection(self):
        return self.db._get_connection()

    def get_by_id(self, message_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM messages WHERE message_id = ? AND is_deleted = 0",
                (message_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_room(self, room_id: str, start_time: str = None, end_time: str = None) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM messages WHERE room_id = ? AND is_deleted = 0"
            params = [room_id]

            if start_time:
                query += " AND send_time >= ?"
                params.append(start_time)
            if end_time:
                query += " AND send_time <= ?"
                params.append(end_time)

            query += " ORDER BY send_time ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def save_message(self, message_id: str, room_id: str, account_id: int, name: str,
                     body: str, send_time: str) -> tuple:
        """Save or update message, returns (is_new, is_updated)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            existing = self.get_by_id(message_id)
            content_hash = self.db.compute_hash(body)
            now = self.db.now_vn()

            if existing:
                if existing['content_hash'] != content_hash:
                    # Message was edited
                    cursor.execute("""
                        INSERT INTO message_versions
                        (message_id, body, content_hash, version_time, change_type)
                        VALUES (?, ?, ?, ?, 'edit')
                    """, (message_id, existing['body'], existing['content_hash'], now))

                    cursor.execute("""
                        UPDATE messages
                        SET body = ?, content_hash = ?, updated_at = ?, is_deleted = 0
                        WHERE message_id = ?
                    """, (body, content_hash, now, message_id))
                    conn.commit()
                    return (False, True)
                return (False, False)
            else:
                # New message
                cursor.execute("""
                    INSERT INTO messages
                    (message_id, room_id, account_id, name, body, send_time,
                     created_at, updated_at, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (message_id, room_id, account_id, name, body, send_time,
                      now, now, content_hash))
                conn.commit()
                return (True, False)
        finally:
            conn.close()

    def save_messages_batch(self, messages: List[Dict], conn=None) -> tuple:
        """Save multiple messages, returns (new_count, updated_count, unchanged_count)"""
        if conn is None:
            with self.db.operation_lock, self.get_connection() as transaction:
                return self.save_messages_batch(messages, transaction)
        counts = [0, 0, 0]
        for msg in messages:
            if not msg.get('message_id') or not msg.get('room_id') or not isinstance(msg.get('body'), str):
                raise ValueError('Tin nhắn thiếu ID, Room hoặc nội dung hợp lệ.')
            now = self.db.now_vn()
            digest = self.db.compute_hash(msg['body'])
            existing = conn.execute('SELECT * FROM messages WHERE message_id=?', (msg['message_id'],)).fetchone()
            if existing:
                changed = existing['content_hash'] != digest or existing['is_deleted'] or any(existing[k] != msg.get(k) for k in ('room_id','account_id','name','send_time'))
                if changed:
                    conn.execute('INSERT INTO message_versions(message_id,body,content_hash,version_time,change_type) VALUES(?,?,?,?,?)',
                                 (msg['message_id'], existing['body'], existing['content_hash'], now, 'edit'))
                    conn.execute('UPDATE messages SET room_id=?,account_id=?,name=?,send_time=?,body=?, content_hash=?, updated_at=?, is_deleted=0 WHERE message_id=?',
                                 (msg['room_id'],msg.get('account_id'),msg.get('name'),msg['send_time'],msg['body'], digest, now, msg['message_id']))
                counts[1 if changed else 2] += 1
            else:
                conn.execute('INSERT INTO messages(message_id,room_id,account_id,name,body,send_time,created_at,updated_at,content_hash) VALUES(?,?,?,?,?,?,?,?,?)',
                             (msg['message_id'], msg['room_id'], msg.get('account_id'), msg.get('name'), msg['body'], msg['send_time'], now, now, digest))
                counts[0] += 1
        return tuple(counts)


class ConfigRepository:
    """Repository for configuration operations"""

    def __init__(self, db: Database):
        self.db = db

    def get_connection(self):
        return self.db._get_connection()

    def get(self, key: str, default=None):
        from ..utils.security import SecretStore, SECRET_KEYS
        if key in SECRET_KEYS:
            return SecretStore(self.db.db_path).get(key) or default
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row['value'])
                except:
                    return row['value']
            return default

    def set(self, key: str, value):
        from ..utils.security import SecretStore, SECRET_KEYS
        if key in SECRET_KEYS:
            with self.db.operation_lock:
                SecretStore(self.db.db_path).set(key, value)
            return
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = self.db.now_vn()
            value = json.dumps(value, ensure_ascii=False)
            cursor.execute("""
                INSERT INTO config (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
            """, (key, str(value), now, str(value), now))
            conn.commit()

    def get_chatwork_config(self) -> Dict:
        """Get Chatwork API configuration"""
        return {
            'api_key': self.get('chatwork_api_key'),
            'room_id': self.get('chatwork_room_id'),
            'room_name': self.get('chatwork_room_name')
        }

    def get_sync_schedule(self) -> Dict:
        """Get sync schedule configuration"""
        return {
            'hour': self.get('sync_hour', 13),
            'minute': self.get('sync_minute', 0),
            'timezone': self.get('sync_timezone', 'Asia/Ho_Chi_Minh'),
            'last_successful_sync': self.get('last_successful_sync'),
            'schedule_enabled': self.get('schedule_enabled', False)
        }

    def get_ai_provider(self) -> Dict:
        """Get AI provider configuration"""
        provider = self.get('ai_provider', 'anthropic')
        profile = self.get('ai_profiles', {}).get(provider)
        if profile:
            from ..utils.security import SecretStore
            return {**profile, 'api_key': SecretStore(self.db.db_path).get('ai:' + provider)}
        return {
            'provider': self.get('ai_provider', 'anthropic'),
            'model': self.get('ai_model'),
            'api_key': self.get('ai_api_key'),
            'base_url': self.get('ai_base_url')
        }


class SyncHistoryRepository:
    """Repository for sync history operations"""

    def __init__(self, db: Database):
        self.db = db

    def get_connection(self):
        return self.db._get_connection()

    def save_sync(self, sync_time: str, source: str, room_id: str, status: str,
                  messages_new: int, messages_updated: int, messages_unchanged: int,
                  error_message: str = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = self.db.now_vn()
            cursor.execute("""
                INSERT INTO sync_history
                (sync_time, source, room_id, status, messages_new, messages_updated,
                 messages_unchanged, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sync_time, source, room_id, status, messages_new, messages_updated,
                  messages_unchanged, error_message, now))
            conn.commit()
            return cursor.lastrowid

    def get_recent(self, limit: int = 50) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sync_history
                ORDER BY sync_time DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_last_successful(self) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sync_history
                WHERE status = 'success'
                ORDER BY sync_time DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None


class ExportSessionRepository:
    """Repository for export session operations"""

    def __init__(self, db: Database):
        self.db = db

    def get_connection(self):
        return self.db._get_connection()

    def create_session(self, session_id: str, month: int, year: int,
                       ai_provider: str = None, ai_model: str = None) -> str:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = self.db.now_vn()
            cursor.execute("""
                INSERT INTO export_sessions
                (session_id, month, year, status, ai_provider, ai_model, created_at, updated_at)
                VALUES (?, ?, ?, 'analyzing', ?, ?, ?, ?)
            """, (session_id, month, year, ai_provider, ai_model, now, now))
            conn.commit()
            return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM export_sessions WHERE session_id = ?",
                          (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_session_by_month(self, month: int, year: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM export_sessions
                WHERE month = ? AND year = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (month, year))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_session(self, session_id: str, status: str = None, file_path: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = self.db.now_vn()
            updates = ["updated_at = ?"]
            params = [now]

            if status:
                updates.append("status = ?")
                params.append(status)
            if file_path:
                updates.append("file_path = ?")
                params.append(file_path)

            params.append(session_id)
            cursor.execute(f"""
                UPDATE export_sessions
                SET {', '.join(updates)}
                WHERE session_id = ?
            """, params)
            conn.commit()

    def save_results(self, session_id: str, results: List[Dict]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = self.db.now_vn()

            for result in results:
                cursor.execute("""
                    INSERT INTO ai_results
                    (session_id, event_id, source_id, employee_name, display_name,
                     employee_code, event_date, event_type, event_subtype, reason,
                     hours_compensation, is_compensated, minutes_not_compensated,
                     minutes_compensated, leave_type, is_excluded, source_message_ids,
                     confidence, needs_review, review_reason, ai_raw_output,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    result.get('event_id'),
                    result.get('source_id'),
                    result.get('employee_name'),
                    result.get('display_name'),
                    result.get('employee_code'),
                    result.get('event_date'),
                    result.get('event_type'),
                    result.get('event_subtype'),
                    result.get('reason'),
                    result.get('hours_compensation'),
                    int(result.get('is_compensated', False)),
                    result.get('minutes_not_compensated', 0),
                    result.get('minutes_compensated', 0),
                    result.get('leave_type'),
                    int(result.get('is_excluded', False)),
                    json.dumps(result.get('source_message_ids', [])),
                    result.get('confidence'),
                    int(result.get('needs_review', False)),
                    result.get('review_reason'),
                    json.dumps(result.get('ai_raw_output', {})),
                    now, now
                ))
            conn.commit()

    def get_results(self, session_id: str, include_excluded: bool = False) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM ai_results WHERE session_id = ?"
            if not include_excluded:
                query += " AND is_excluded = 0"
            query += " ORDER BY event_date ASC"
            cursor.execute(query, (session_id,))
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                if r.get('source_message_ids'):
                    r['source_message_ids'] = json.loads(r['source_message_ids'])
                if r.get('ai_raw_output'):
                    r['ai_raw_output'] = json.loads(r['ai_raw_output'])
                results.append(r)
            return results

    def save_correction(self, result_id: int, session_id: str, field_name: str,
                       old_value: str, new_value: str, correction_type: str = 'manual'):
        allowed = {'employee_name', 'display_name', 'employee_code', 'event_date',
                   'event_type', 'event_subtype', 'reason', 'hours_compensation',
                   'is_compensated', 'minutes_not_compensated', 'minutes_compensated',
                   'leave_type', 'is_excluded', 'needs_review', 'review_reason'}
        if field_name not in allowed:
            raise ValueError('Invalid correction field')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = self.db.now_vn()
            cursor.execute(
                f'UPDATE ai_results SET {field_name} = ?, updated_at = ? '
                'WHERE result_id = ? AND session_id = ?',
                (new_value, now, result_id, session_id))
            if cursor.rowcount != 1:
                raise ValueError('Result not found in session')
            cursor.execute("""
                INSERT INTO corrections
                (result_id, session_id, field_name, old_value, new_value,
                 corrected_at, correction_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (result_id, session_id, field_name, old_value, new_value, now, correction_type))
            conn.commit()

    def get_corrections(self, session_id: str) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM corrections
                WHERE session_id = ?
                ORDER BY corrected_at DESC
            """, (session_id,))
            return [dict(row) for row in cursor.fetchall()]


class ActionEventRepository:
    """Repository for action events (unified history)"""

    def __init__(self, db: Database):
        self.db = db

    def get_connection(self):
        return self.db._get_connection()

    def log_event(self, operation_id: str, action_type: str, source: str,
                  status: str, session_id: str = None, summary: str = None,
                  details: Dict = None, file_path: str = None, error_message: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = self.db.now_vn()
            cursor.execute("""
                INSERT INTO action_events
                (operation_id, session_id, action_type, action_time, source, status,
                 summary, details, file_path, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                operation_id,
                session_id,
                action_type,
                now,
                source,
                status,
                summary,
                json.dumps(details, ensure_ascii=False) if details else None,
                file_path,
                error_message,
                now
            ))
            conn.commit()

    def get_events(self, start_time: str = None, end_time: str = None,
                   action_types: List[str] = None, statuses: List[str] = None,
                   limit: int = 100) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM action_events WHERE 1=1"
            params = []

            if start_time:
                query += " AND action_time >= ?"
                params.append(start_time)
            if end_time:
                query += " AND action_time <= ?"
                params.append(end_time)
            if action_types:
                query += f" AND action_type IN ({','.join(['?']*len(action_types))})"
                params.extend(action_types)
            if statuses:
                query += f" AND status IN ({','.join(['?']*len(statuses))})"
                params.extend(statuses)

            query += " ORDER BY action_time DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                if r.get('details'):
                    r['details'] = json.loads(r['details'])
                results.append(r)
            return results

    def get_by_session(self, session_id: str) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM action_events
                WHERE session_id = ?
                ORDER BY action_time ASC
            """, (session_id,))
            results = []
            for row in cursor.fetchall():
                r = dict(row)
                if r.get('details'):
                    r['details'] = json.loads(r['details'])
                results.append(r)
            return results
