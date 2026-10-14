# -*- coding: utf-8 -*-
"""
Sync service for message synchronization
"""
import os
import sys
import json
import hashlib
import socket
import threading
from datetime import datetime
from typing import Dict, Optional
import pytz

from ..adapters.chatwork_adapter import ChatworkAdapter, ChatworkAPIError
from ..models.database import (
    Database, MessageRepository, ConfigRepository,
    SyncHistoryRepository, ActionEventRepository
)

Vietnam_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
LOCK_FILE = "data/sync.lock"


def _file_lock(lock_file, exclusive=True, blocking=False):
    """Cross-platform file lock (Windows uses msvcrt, Unix uses fcntl)"""
    if sys.platform == 'win32':
        import msvcrt
        try:
            if exclusive:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBRLCK, 1)
            return True
        except (IOError, OSError):
            return False
    else:
        import fcntl
        try:
            if exclusive:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            else:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            return True
        except (IOError, OSError):
            return False


def _file_unlock(lock_file):
    """Cross-platform file unlock"""
    if sys.platform == 'win32':
        import msvcrt
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        except:
            pass
    else:
        import fcntl
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        except:
            pass


class SyncServiceError(ValueError):
    """Custom exception for sync service errors"""
    pass


class SyncService:
    """Service for synchronizing messages from Chatwork"""

    def __init__(self, db: Database, config_repo: ConfigRepository,
                 message_repo: MessageRepository, sync_repo: SyncHistoryRepository,
                 action_repo: ActionEventRepository, app_path: str):
        self.db = db
        self.config_repo = config_repo
        self.message_repo = message_repo
        self.sync_repo = sync_repo
        self.action_repo = action_repo
        self.app_path = app_path
        self._sync_guard = threading.Lock()

    def _acquire_lock(self) -> bool:
        """Acquire sync lock to prevent concurrent syncs"""
        if not self._sync_guard.acquire(blocking=False):
            return False
        lock_path = os.path.join(self.app_path, LOCK_FILE)
        try:
            os.makedirs(os.path.dirname(lock_path), exist_ok=True)
            self._lock_file = open(lock_path, 'r+b' if os.path.exists(lock_path) else 'w+b')
            self._lock_file.seek(0)
            if not _file_lock(self._lock_file, exclusive=True, blocking=False):
                self._lock_file.close()
                self._sync_guard.release()
                return False
            self._lock_file.seek(0)
            self._lock_file.write(json.dumps({
                'pid': os.getpid(),
                'start_time': datetime.now(Vietnam_TZ).isoformat()
            }).encode('utf-8'))
            self._lock_file.truncate()
            self._lock_file.flush()
            return True
        except (IOError, OSError):
            if hasattr(self, '_lock_file'):
                try:
                    self._lock_file.close()
                except:
                    pass
            self._sync_guard.release()
            return False

    def _release_lock(self):
        """Release sync lock"""
        if getattr(self, '_lock_file', None) is not None:
            try:
                self._lock_file.seek(0)
                _file_unlock(self._lock_file)
                self._lock_file.close()
            finally:
                self._lock_file = None
                self._sync_guard.release()

    def _get_chatwork_adapter(self) -> ChatworkAdapter:
        """Get Chatwork adapter with current config"""
        config = self.config_repo.get_chatwork_config()
        if not config.get('api_key'):
            raise SyncServiceError("Chatwork API key not configured")
        return ChatworkAdapter(config['api_key'])

    def sync(self, source='manual', slot=None, full_history=False):
        operation_id='SYNC-'+__import__('uuid').uuid4().hex[:12]
        with self.db.operation_lock:
            if not self._acquire_lock():
                raise SyncServiceError('Một lần đồng bộ đang chạy.')
            try:
                config=self.config_repo.get_chatwork_config()
                if not config.get('api_key'):
                    raise SyncServiceError('Chatwork API key not configured')
                if not config.get('room_id'):
                    raise SyncServiceError('Chatwork room not selected')
                room=config['room_id']
                if slot and self.config_repo.get('completed_slot:'+room)==slot:
                    return {'success':True,'skipped':True,'operation_id':operation_id}
                self.action_repo.log_event(operation_id,'sync',source,'running',summary='Bắt đầu đồng bộ.')
                adapter=self._get_chatwork_adapter()

                # Fetch only the documented recent window; SQLite accumulates history.
                messages=adapter.get_recent_messages(room, limit=100)
                normalized=[adapter.normalize_message({**m,'room_id':room}) for m in messages]
                timestamp=datetime.now(Vietnam_TZ).isoformat()
                with self.db._get_connection() as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    counts=self.message_repo.save_messages_batch(normalized,conn)
                    conn.execute('INSERT INTO sync_history(sync_time,source,room_id,status,messages_new,messages_updated,messages_unchanged,created_at) VALUES(?,?,?,?,?,?,?,?)',
                                 (timestamp,source,room,'success',*counts,timestamp))
                    settings={'last_successful_sync':timestamp,'last_successful_sync:'+room:timestamp,
                              'coverage_warning:'+room:'Chatwork API chỉ trả tối đa 100 tin gần nhất. Database tích lũy qua các lần đồng bộ; lịch sử chưa lưu cần nhập MessageLog.'}
                    if slot:settings['completed_slot:'+room]=slot
                    for key,value in settings.items():
                        conn.execute('INSERT INTO config(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',
                                     (key,json.dumps(value,ensure_ascii=False),timestamp))
                self.action_repo.log_event(operation_id,'sync',source,'success',summary=f'Đồng bộ: {counts[0]} mới, {counts[1]} sửa, {counts[2]} không đổi.',details={'room_id':room})
                return {'success':True,'messages_new':counts[0],'messages_updated':counts[1],'messages_unchanged':counts[2],'operation_id':operation_id}
            except Exception as error:
                # Never retain response bodies, tokens or URLs from transport exceptions.
                safe=str(error) if isinstance(error,SyncServiceError) else 'Đồng bộ thất bại. Kiểm tra mạng, API key và quyền truy cập Room.'
                self.action_repo.log_event(operation_id,'sync',source,'failed',error_message=safe)
                raise SyncServiceError(safe) from None
            finally:
                self._release_lock()

    def catch_up(self,source='catchup'):
        from ..scheduler.timing import due_slot
        schedule=self.config_repo.get_sync_schedule()
        if source in {'scheduled','catchup'} and not schedule.get('schedule_enabled',False):
            return {'skipped':True}
        config=self.config_repo.get_chatwork_config()
        if not config.get('room_id') or not config.get('api_key'):
            return {'skipped':True}
        room=config['room_id']
        schedule['effective_from']=self.config_repo.get('schedule_effective_from')
        last=self.config_repo.get('last_successful_sync:'+room)
        slot=due_slot(schedule,last)
        if not slot and last:
            # On next-day login/open, collect messages sent after yesterday's
            # successful run even if today's configured time has not arrived.
            now=datetime.now(Vietnam_TZ)
            previous=datetime.fromisoformat(last)
            previous=Vietnam_TZ.localize(previous) if previous.tzinfo is None else previous.astimezone(Vietnam_TZ)
            effective=schedule.get('effective_from')
            ready=not effective or now>=datetime.fromisoformat(effective)
            if ready and previous.date()<now.date():
                slot='catchup:'+now.date().isoformat()
                source='catchup' if source=='scheduled' else source
        if not slot:return {'skipped':True}
        return self.sync(source,slot)

    def get_status(self):
        cfg=self.config_repo.get_chatwork_config()
        room=cfg.get('room_id')
        schedule=self.config_repo.get_sync_schedule()
        with self.db._get_connection() as conn:
            latest=conn.execute("SELECT * FROM sync_history WHERE room_id=? AND status='success' ORDER BY sync_id DESC LIMIT 1",(room,)).fetchone()
        return {'room_id':room,'room_name':cfg.get('room_name'),
                'last_successful_sync':self.config_repo.get('last_successful_sync:'+str(room)),
                'sync_hour':schedule['hour'],'sync_minute':schedule['minute'],'timezone':schedule['timezone'],
                'schedule_enabled':schedule['schedule_enabled'],
                'coverage_warning':self.config_repo.get('coverage_warning:'+str(room)),
                'message_count':len(self.message_repo.get_by_room(room)) if room else 0,
                'last_sync_result':dict(latest) if latest else None}

    def get_messages(self,room_id=None,start_time=None,end_time=None,sender=None,keyword=None,limit=100):
        room_id=room_id or self.config_repo.get('chatwork_room_id')
        if not room_id:return []
        messages=self.message_repo.get_by_room(room_id)
        if start_time:messages=[m for m in messages if m['send_time'][:10]>=start_time[:10]]
        if end_time:messages=[m for m in messages if m['send_time'][:10]<=end_time[:10]]
        if sender:messages=[m for m in messages if sender.casefold() in (m.get('name') or '').casefold()]
        if keyword:messages=[m for m in messages if keyword.casefold() in m['body'].casefold()]
        return messages[-max(1,min(int(limit),5000)):][::-1]
