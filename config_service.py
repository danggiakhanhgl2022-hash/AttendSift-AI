"""Validated settings, verified schedule, data-only backups."""
import json
import os
from pathlib import Path
import sqlite3
import uuid
from ..adapters.chatwork_adapter import ChatworkAdapter
from ..adapters.ai_adapters import create_ai_adapter
from ..utils.security import SecretStore, SecretError
from ..scheduler.timing import next_run


class ConfigServiceError(ValueError):
    pass


class ConfigService:
    def __init__(self,db,config_repo,action_repo,app_path):
        self.db,self.config_repo,self.action_repo,self.app_path=db,config_repo,action_repo,app_path

    def _log(self,kind,summary,status='success',details=None):
        self.action_repo.log_event('CFG-'+uuid.uuid4().hex[:12],kind,'user',status,summary=summary,details=details)

    def _public(self,config):
        config=dict(config)
        config['has_api_key']=bool(config.pop('api_key',None))
        config['api_key_masked']='Đã cấu hình' if config['has_api_key'] else ''
        return config

    def get_chatwork_config(self):
        try:return self._public(self.config_repo.get_chatwork_config())
        except SecretError:return {'has_api_key':False,'room_id':self.config_repo.get('chatwork_room_id'),'room_name':self.config_repo.get('chatwork_room_name'),'key_error':'Vui lòng nhập lại API key trên tài khoản này.'}

    def get_ai_config(self):
        try:return self._public(self.config_repo.get_ai_provider())
        except SecretError:return {'has_api_key':False,'provider':self.config_repo.get('ai_provider','anthropic'),'key_error':'Vui lòng nhập lại API key AI.'}

    def test_chatwork_connection(self,api_key):
        try:return {'success':True,'account':ChatworkAdapter(api_key).test_connection()}
        except Exception:return {'success':False,'error':'Không kết nối được Chatwork. Kiểm tra API key, mạng và quyền truy cập.'}

    def save_chatwork_config(self,api_key,room_id=None,room_name=None):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ConfigServiceError('API key phải là chuỗi hợp lệ.')
        if room_id is not None and (isinstance(room_id, bool) or not isinstance(room_id, (str, int)) or not str(room_id).isdigit()):
            raise ConfigServiceError('Room ID phải là số hợp lệ.')
        with self.db.operation_lock:
            result=self.test_chatwork_connection(api_key)
            if not result['success']:
                self._log('config_chatwork','Kiểm tra Chatwork thất bại.','failed')
                raise ConfigServiceError(result['error'])
            match = None
            if room_id is not None:
                try:
                    match = next((r for r in ChatworkAdapter(api_key).get_rooms() if str(r['room_id']) == str(room_id)), None)
                except Exception:
                    raise ConfigServiceError('Không kiểm tra được quyền truy cập Room.') from None
                if not match:
                    raise ConfigServiceError('Room không thuộc danh sách được API cấp quyền.')
            previous_key = self.config_repo.get('chatwork_api_key')
            try:
                with self.db._get_connection() as conn:
                    conn.execute('BEGIN IMMEDIATE')
                    if match:
                        for key, value in {'chatwork_room_id': str(room_id), 'chatwork_room_name': match['name']}.items():
                            conn.execute('INSERT INTO config(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at', (key, json.dumps(value, ensure_ascii=False), self.db.now_vn()))
                    self.config_repo.set('chatwork_api_key', api_key)
            except Exception:
                self.config_repo.set('chatwork_api_key', previous_key)
                raise
            self._log('config_chatwork','Đã cập nhật kết nối Chatwork; API key đã cập nhật.')
            return {'success':True,'message':'Đã kiểm tra và lưu kết nối Chatwork.'}

    def get_rooms(self):
        key=self.config_repo.get('chatwork_api_key')
        if not key:return []
        return [{'room_id':str(r['room_id']),'name':r['name']} for r in ChatworkAdapter(key).get_rooms()]

    def save_room(self,room_id,room_name=None):
        with self.db.operation_lock:
            match=next((r for r in self.get_rooms() if str(r['room_id'])==str(room_id)),None)
            if not match:raise ConfigServiceError('Room không thuộc danh sách được API cấp quyền.')
            old=self.config_repo.get('chatwork_room_id')
            self.config_repo.set('chatwork_room_id',str(room_id))
            self.config_repo.set('chatwork_room_name',match['name'])
            self._log('config_room','Đã chọn Room; mốc đồng bộ được quản lý riêng theo Room.',details={'old_room_id':old,'room_id':str(room_id)})
            return {'success':True,'message':'Đã chọn Room. Phiên đã tạo giữ nguyên Room cũ.'}

    def test_ai_connection(self,provider,api_key,model=None,base_url=None):
        if not isinstance(provider, str) or not provider.strip():
            raise ConfigServiceError('Nhà cung cấp AI phải là chuỗi hợp lệ.')
        if api_key is not None and not isinstance(api_key, str):
            raise ConfigServiceError('API key phải là chuỗi hợp lệ.')
        api_key=api_key or SecretStore(self.db.db_path).get('ai:'+provider)
        if not api_key and provider==self.config_repo.get('ai_provider','anthropic'):
            api_key=self.config_repo.get('ai_api_key')
        try:
            return {'success':True,'data':create_ai_adapter(provider,api_key,model,base_url).test_connection()}
        except Exception as error:
            from ..adapters.ai_adapters import AIHTTPError, AIResponseError
            if isinstance(error, AIHTTPError):
                raise ConfigServiceError(str(AIHTTPError(error.status))) from None
            if isinstance(error, AIResponseError):
                raise ConfigServiceError(str(AIResponseError(error.code))) from None
            raise ConfigServiceError('Không kết nối được AI. Kiểm tra nhà cung cấp, API key, model và địa chỉ dịch vụ.') from None

    def save_ai_config(self,provider,api_key=None,model=None,base_url=None,set_default=True):
        if not isinstance(provider, str) or not provider.strip():
            raise ConfigServiceError('Nhà cung cấp AI phải là chuỗi hợp lệ.')
        if type(set_default) is not bool:
            raise ConfigServiceError('set_default phải là boolean.')
        with self.db.operation_lock:
            profiles=self.config_repo.get('ai_profiles',{})
            previous=profiles.get(provider,{})
            store=SecretStore(self.db.db_path)
            key=api_key or store.get('ai:'+provider)
            result=self.test_ai_connection(provider,key,model,base_url)
            if not result['success']:raise ConfigServiceError('Không kiểm tra được AI.')
            store.set('ai:'+provider,key)
            profiles[provider]={'provider':provider,'model':model or result['data']['model'],'base_url':base_url}
            self.config_repo.set('ai_profiles',profiles)
            if set_default:
                self.config_repo.set('ai_provider',provider)
            self._log('config_ai','Đã cập nhật kết nối AI; API key đã cập nhật.',details={'provider':provider,'set_default':bool(set_default)})
            return {'success':True,'message':'Đã kiểm tra và lưu AI.'}

    def get_sync_schedule(self):return self.config_repo.get_sync_schedule()

    def save_sync_schedule(self,hour,minute,timezone='Asia/Ho_Chi_Minh',scheduler=None):
        effective=next_run(hour,minute).isoformat()
        if scheduler is None:
            from ..scheduler.windows_scheduler import WindowsScheduler
            scheduler=WindowsScheduler(self.app_path)
        with self.db.operation_lock:
            old=self.get_sync_schedule()
            self.config_repo.set('schedule_requested',{'hour':hour,'minute':minute})
            result=scheduler.update_schedule(hour,minute)
            if result['success']:
                for key,value in {'sync_hour':hour,'sync_minute':minute,'sync_timezone':timezone,
                                  'schedule_effective_from':effective,'schedule_enabled':True}.items():
                    self.config_repo.set(key,value)
            self.config_repo.set('schedule_last_result',result)
            self._log('config_schedule',result['message'],'success' if result['success'] else 'failed',
                      {'before':{'hour':old['hour'],'minute':old['minute']},'requested':{'hour':hour,'minute':minute},'applied':result.get('applied')})
            return {**result,'scheduler':result,'effective_from':effective if result['success'] else None}

    @staticmethod
    def validate_backup(path):
        uri=Path(path).resolve().as_uri()+'?mode=ro'
        conn=sqlite3.connect(uri,uri=True)
        try:
            if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ConfigServiceError('Backup bị hỏng.')
            names={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required={'config','messages','message_versions','export_sessions','ai_results','corrections','action_events','sync_history'}
            if not required.issubset(names):raise ConfigServiceError('Backup không đúng cấu trúc ứng dụng.')
            columns={'config':{'key','value','updated_at'},'messages':{'message_id','body','room_id','send_time','content_hash'},
                     'message_versions':{'message_id','body','content_hash'},'export_sessions':{'session_id','status','month','year','file_path'},
                     'ai_results':{'result_id','session_id','source_message_ids','ai_raw_output'},'corrections':{'result_id','session_id','old_value','new_value'},
                     'action_events':{'operation_id','action_type','status','details'},'sync_history':{'room_id','status','sync_time'}}
            for table,fields in columns.items():
                if not fields.issubset({row[1] for row in conn.execute('PRAGMA table_info('+table+')')}):
                    raise ConfigServiceError('Backup thiếu cột dữ liệu bắt buộc: '+table)
            if conn.execute('PRAGMA foreign_key_check').fetchone():raise ConfigServiceError('Backup có liên kết dữ liệu không hợp lệ.')
            if conn.execute('PRAGMA user_version').fetchone()[0]>2:raise ConfigServiceError('Backup thuộc phiên bản mới hơn.')
            if conn.execute("SELECT count(*) FROM config WHERE key IN ('chatwork_api_key','ai_api_key')").fetchone()[0]:
                raise ConfigServiceError('Backup cũ chứa key chưa được chuyển đổi. Hãy nâng cấp database gốc trước.')
        finally:conn.close()

    def create_backup(self):
        with self.db.operation_lock:
            folder=Path(self.app_path)/'backups';folder.mkdir(parents=True,exist_ok=True)
            path=folder/('backup_'+__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S%f')+'.db')
            with self.db._get_connection() as source:
                target=sqlite3.connect(path)
                try:source.backup(target)
                finally:target.close()
            self.validate_backup(path)
            self._log('backup','Đã sao lưu dữ liệu, không bao gồm API key.')
            files=sorted(folder.glob('backup_*.db'),key=lambda p:p.stat().st_mtime,reverse=True)
            for old in files[10:]:old.unlink()
            return {'success':True,'backup_path':str(path),'message':'Đã sao lưu dữ liệu.'}

    def list_backups(self):
        folder=Path(self.app_path)/'backups'
        return [{'name':p.name,'size':p.stat().st_size,'created':__import__('datetime').datetime.fromtimestamp(p.stat().st_mtime).isoformat()} for p in sorted(folder.glob('*.db'),reverse=True)]

    def restore_backup(self,backup_path):
        with self.db.operation_lock:
            folder=(Path(self.app_path)/'backups').resolve()
            path=(folder/backup_path).resolve()
            if path.parent!=folder:raise ConfigServiceError('Đường dẫn backup không hợp lệ.')
            self.validate_backup(path)
            # Pin the source before backup rotation can remove it.
            source=sqlite3.connect(':memory:')
            disk=sqlite3.connect(path)
            try:disk.backup(source)
            finally:disk.close()
            try:
                self.create_backup()
                with self.db._get_connection() as target:source.backup(target)
            finally:source.close()
            from ..models.migrations import migrate
            migrate(self.db)
            self._log('restore','Đã khôi phục dữ liệu. API key trên máy này được giữ riêng.')
            return {'success':True,'message':'Đã khôi phục. Kiểm tra lại kết nối và lưu lịch Windows nếu giờ thay đổi.'}

    def get_app_version(self):
        from .. import __version__
        return {'version':__version__,'data_path':str(Path(self.app_path)/'data'),'backup_count':len(self.list_backups())}
