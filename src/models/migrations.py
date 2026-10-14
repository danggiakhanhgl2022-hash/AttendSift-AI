"""Additive migrations; legacy sessions stay readable but cannot be re-exported."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from ..utils.security import SecretStore, SECRET_KEYS


def migrate(db):
    with db._get_connection() as conn:
        version = conn.execute('PRAGMA user_version').fetchone()[0]
        if version > 2:
            raise ValueError('Database thuộc phiên bản mới hơn ứng dụng.')
        # Move keys before creating a data-only migration backup.
        rows = conn.execute("SELECT key,value FROM config WHERE key IN ('chatwork_api_key','ai_api_key')").fetchall()
        store = SecretStore(db.db_path)
        for row in rows:
            value = row['value']
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                pass
            store.set(row['key'], value)
            if isinstance(value,str) and value:
                for field in ('details','summary','error_message'):
                    conn.execute('UPDATE action_events SET '+field+'=replace('+field+',?,?) WHERE instr('+field+',?)>0',
                                 (value,'[Đã ẩn API key]',value))
        conn.execute('PRAGMA secure_delete=ON')
        conn.execute("DELETE FROM config WHERE key IN ('chatwork_api_key','ai_api_key')")
    if version == 2:
        return
    with db._get_connection() as conn:
        populated = conn.execute('SELECT count(*) FROM messages').fetchone()[0] or conn.execute('SELECT count(*) FROM export_sessions').fetchone()[0]
        if populated:
            folder = Path(db.db_path).parent / 'migration-backups'
            folder.mkdir(exist_ok=True)
            destination = folder / (f'before-v{version}-' + datetime.now().strftime('%Y%m%d%H%M%S%f') + '.db')
            target = sqlite3.connect(destination)
            try:
                conn.backup(target)
            finally:
                target.close()
        additions = {
            'export_sessions': {'room_id':'TEXT', 'snapshot':'TEXT', 'request_id':'TEXT',
                'is_draft':'INTEGER DEFAULT 0', 'risk_message':'TEXT', 'file_hash':'TEXT',
                'period_start':'TEXT', 'period_end':'TEXT', 'ai_settings':'TEXT', 'error_message':'TEXT',
                'analysis_checkpoint':'TEXT'},
            'ai_results': {'person_id':'TEXT', 'payload':'TEXT', 'validation_errors':'TEXT',
                           'review_state':"TEXT DEFAULT 'pending'"}}
        for table, fields in additions.items():
            columns = {row[1] for row in conn.execute('PRAGMA table_info(' + table + ')')}
            for name, kind in fields.items():
                if name not in columns:
                    conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} {kind}')
        conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_session_request ON export_sessions(request_id) WHERE request_id IS NOT NULL')
        conn.execute('PRAGMA user_version=2')
