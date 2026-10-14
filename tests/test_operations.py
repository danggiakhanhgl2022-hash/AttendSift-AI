import copy
from datetime import datetime
import json
from pathlib import Path
import re
import sqlite3
from unittest.mock import Mock,patch
import pytest
from src.models.database import Database,ConfigRepository,MessageRepository,ActionEventRepository
from src.scheduler.timing import next_run,due_slot,TZ
from src.services.config_service import ConfigService,ConfigServiceError
from src.utils.security import SecretStore,dpapi,SecretError
from src.adapters.ai_adapters import create_ai_adapter,AIAdapterError
from src.adapters.chatwork_adapter import ChatworkAdapter,ChatworkAPIError


def test_batch_rollback(temp_db):
    repo=MessageRepository(temp_db)
    with pytest.raises(ValueError):repo.save_messages_batch([
        {'message_id':'1','room_id':'r','body':'test','send_time':'2026-09-01T10:00:00+07:00'},
        {'message_id':'','room_id':'r','body':'invalid','send_time':'2026-09-01T10:00:00+07:00'}])
    assert repo.get_by_room('r')==[]


def test_sender_metadata_change_invalidates_snapshot_input(temp_db):
    repo=MessageRepository(temp_db)
    message={'message_id':'m','room_id':'r','body':'same','account_id':1,'name':'A','send_time':'2026-09-01T10:00:00+07:00'}
    repo.save_messages_batch([message])
    assert repo.save_messages_batch([{**message,'name':'B'}])==(0,1,0)
    assert repo.get_by_id('m')['name']=='B'


def test_chatwork_rate_limit_retry_preserves_error_semantics():
    adapter=ChatworkAdapter('fake')
    limited=Mock(status_code=429,headers={'Retry-After':'1'});good=Mock(status_code=200);good.json.return_value=[]
    with patch.object(adapter.session,'request',side_effect=[limited,good]) as call, patch('src.adapters.chatwork_adapter.time.sleep') as sleep:
        assert adapter.get_recent_messages('r')==[]
        assert call.call_count==2 and sleep.call_count==1


def test_dpapi_not_plaintext_and_other_user_error(temp_db):
    repo=ConfigRepository(temp_db);repo.set('chatwork_api_key','fake-secret-test')
    assert repo.get('chatwork_api_key')=='fake-secret-test'
    assert b'fake-secret-test' not in SecretStore(temp_db.db_path).path.read_bytes()
    with temp_db._get_connection() as c:assert c.execute("SELECT count(*) FROM config WHERE key='chatwork_api_key'").fetchone()[0]==0
    with patch('src.utils.security.dpapi',side_effect=SecretError('Nhập lại API key')):
        public=ConfigService(temp_db,repo,ActionEventRepository(temp_db),'.').get_chatwork_config()
        assert not public['has_api_key'] and public['key_error']


def test_migration_preserves_legacy_and_moves_secret(temp_db):
    repo=MessageRepository(temp_db)
    repo.save_message('old','r',1,'Người thử nghiệm','Giữ lịch sử','2026-09-01T10:00:00+07:00')
    with temp_db._get_connection() as c:
        c.execute('PRAGMA user_version=0')
        c.execute("INSERT INTO config(key,value,updated_at) VALUES('chatwork_api_key','legacy-fake-key','now')")
    again=Database(temp_db.db_path)
    assert MessageRepository(again).get_by_id('old')['body']=='Giữ lịch sử'
    assert ConfigRepository(again).get('chatwork_api_key')=='legacy-fake-key'
    backups=list((Path(temp_db.db_path).parent/'migration-backups').glob('*.db'))
    assert backups
    with sqlite3.connect(backups[-1]) as c:
        assert c.execute("SELECT count(*) FROM config WHERE key='chatwork_api_key'").fetchone()[0]==0


def test_backup_has_no_keys_and_invalid_restore_keeps_data(temp_db,tmp_path):
    repo=ConfigRepository(temp_db);repo.set('chatwork_api_key','fake-secret');repo.set('marker','before')
    service=ConfigService(temp_db,repo,ActionEventRepository(temp_db),str(tmp_path))
    path=service.create_backup()['backup_path']
    with sqlite3.connect(path) as c:assert c.execute("SELECT count(*) FROM config WHERE key LIKE '%api_key%'").fetchone()[0]==0
    bad=tmp_path/'backups'/'bad.db';bad.write_bytes(b'bad')
    with pytest.raises(sqlite3.DatabaseError):service.restore_backup('bad.db')
    assert repo.get('marker')=='before'


def test_schedule_failure_does_not_change_applied_time(temp_db,tmp_path):
    repo=ConfigRepository(temp_db);repo.set('sync_hour',13)
    service=ConfigService(temp_db,repo,ActionEventRepository(temp_db),str(tmp_path))
    scheduler=Mock();scheduler.update_schedule.return_value={'success':False,'applied':{'hour':13,'minute':0},'message':'Không áp dụng được lịch'}
    result=service.save_sync_schedule(14,30,scheduler=scheduler)
    assert not result['success'] and repo.get('sync_hour')==13
    assert repo.get('schedule_requested')=={'hour':14,'minute':30}
    scheduler.update_schedule.return_value={'success':True,'applied':{'hour':14,'minute':30},'message':'Đã áp dụng'}
    assert service.save_sync_schedule(14,30,scheduler=scheduler)['success']
    assert repo.get('sync_hour')==14 and repo.get('sync_minute')==30


def test_timing_month_end_and_configured_recovery():
    now=TZ.localize(datetime(2026,9,30,15))
    assert next_run(14,30,now).isoformat().startswith('2026-10-01T14:30')
    morning=TZ.localize(datetime(2026,9,30,14))
    schedule={'hour':14,'minute':30,'effective_from':'2026-09-30T14:30:00+07:00'}
    assert due_slot(schedule,None,morning) is None
    assert due_slot(schedule,None,now).startswith('2026-09-30T14:30')
    assert due_slot(schedule,'2026-09-30T14:31:00+07:00',now) is None


def test_scheduler_xml_daily_recovery_and_unicode(tmp_path):
    from src.scheduler.windows_scheduler import WindowsScheduler,NS
    import xml.etree.ElementTree as ET
    scheduler=WindowsScheduler(str(tmp_path/'thư mục có dấu'))
    root=ET.fromstring(scheduler._xml(14,30))
    get=lambda name:root.findtext('.//{'+NS+'}'+name)
    assert get('DaysInterval')=='1' and get('StartWhenAvailable')=='true'
    assert get('MultipleInstancesPolicy')=='IgnoreNew' and get('Arguments').endswith(' --sync')
    assert 'thư mục có dấu' in get('Arguments') and 'T14:30:00' in get('StartBoundary')
    assert root.find('.//{'+NS+'}LogonTrigger') is not None
    assert get('Delay')=='PT30S'
    assert get('LogonType')=='InteractiveToken'
    assert get('Interval')=='PT10M' and get('Count')=='144'


def test_scheduler_never_deletes_existing_before_success(tmp_path):
    from src.scheduler.windows_scheduler import WindowsScheduler
    scheduler=WindowsScheduler(str(tmp_path))
    old={'hour':13,'minute':0,'xml':'old'}
    with patch.object(scheduler,'get_task_status',return_value=old),patch.object(scheduler,'_register',return_value=(False,'','error')),patch.object(scheduler,'delete_task') as delete:
        assert not scheduler.update_schedule(14,30)['success'];delete.assert_not_called()


def test_scheduler_requires_verified_logon_and_network_retry(tmp_path):
    from src.scheduler.windows_scheduler import WindowsScheduler
    (tmp_path/'main.py').write_text('pass',encoding='utf-8')
    scheduler=WindowsScheduler(str(tmp_path))
    status={'hour':14,'minute':30,'daily':True,'start_when_available':True,
            'arguments':scheduler.arguments,'path_changed':False,'automatic_recovery':True}
    with patch.object(scheduler,'get_task_status',side_effect=[None,status]),patch.object(scheduler,'_register',return_value=(True,'','')):
        assert scheduler.update_schedule(14,30)['success']
    with patch.object(scheduler,'get_task_status',side_effect=[None,{**status,'automatic_recovery':False},None]),patch.object(scheduler,'_register',return_value=(True,'','')),patch.object(scheduler,'delete_task') as cleanup:
        assert not scheduler.update_schedule(14,30)['success']
        cleanup.assert_called_once()


@pytest.mark.parametrize('provider',['openai','custom','anthropic','gemini'])
def test_provider_tests_make_real_http_request_mocked(provider):
    response=Mock(status_code=200);response.json.return_value={'data':[], 'candidates':[
        {'finishReason':'STOP','content':{'parts':[{'text':'{"events":[]}'}]}}]}
    with patch('src.adapters.ai_adapters.requests.request',return_value=response) as http:
        adapter=create_ai_adapter(provider,'fake-key')
        assert adapter.test_connection()['status']=='ok'
        assert http.call_args.args[0]==('POST' if provider=='gemini' else 'GET')
        assert 'fake-key' not in http.call_args.args[1]


def test_gemini_retries_temporary_service_failure_only():
    unavailable=Mock(status_code=503)
    success=Mock(status_code=200)
    success.json.return_value={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'{"events":[]}'}]}}]}
    adapter=create_ai_adapter('gemini','fake-key')
    with patch('src.adapters.ai_adapters.requests.request',side_effect=[unavailable,success]) as http, patch('src.adapters.ai_adapters.time.sleep'):
        assert adapter.test_connection()['status']=='ok'
        assert http.call_count==2
    with patch('src.adapters.ai_adapters.requests.request',return_value=Mock(status_code=404)) as http:
        with pytest.raises(AIAdapterError,match='Model không khả dụng'):
            adapter.test_connection()
        assert http.call_count==1


def test_gemini_truncated_result_and_timeout_are_distinct():
    import requests
    from src.adapters.ai_adapters import AIResponseError
    adapter=create_ai_adapter('gemini','fake-key')
    with patch.object(adapter,'_request',return_value={'candidates':[{'finishReason':'MAX_TOKENS'}]}):
        with pytest.raises(AIResponseError) as error:adapter.analyze_attendance([],9,2026)
        assert error.value.code=='truncated'
    with patch('src.adapters.ai_adapters.requests.request',side_effect=requests.ReadTimeout('secret-in-url')):
        with pytest.raises(AIResponseError) as error:adapter.test_connection()
        assert error.value.code=='timeout'
        assert 'secret-in-url' not in str(error.value)


def test_ai_bad_json_and_http_errors_redacted():
    adapter=create_ai_adapter('openai','fake-key')
    with pytest.raises(AIAdapterError):adapter._parse_response('{invalid')
    with pytest.raises(AIAdapterError):adapter._parse_response('{"events":[123]}')
    response=Mock(status_code=401)
    with patch('src.adapters.ai_adapters.requests.request',return_value=response):
        with pytest.raises(AIAdapterError) as error:adapter.test_connection()
        assert 'fake-key' not in str(error.value)


def test_chatwork_no_fake_pagination_and_204():
    adapter=ChatworkAdapter('fake')
    with patch.object(adapter,'_request',return_value=[]) as call:
        assert adapter.get_recent_messages('r')==[]
        assert call.call_args.kwargs['params']=={'force':1}
    response=Mock(status_code=204)
    with patch.object(adapter.session,'request',return_value=response):assert adapter.get_recent_messages('r')==[]


def test_chatwork_historical_pagination_rejected_without_http():
    adapter=ChatworkAdapter('fake')
    with patch.object(adapter,'_request') as http:
        with pytest.raises(ChatworkAPIError,match='không hỗ trợ phân trang'):
            adapter.get_messages_before('r',123)
        http.assert_not_called()


@pytest.mark.parametrize('status',[401,403,404,500])
def test_chatwork_error_not_empty_success(status):
    adapter=ChatworkAdapter('fake');response=Mock(status_code=status)
    with patch.object(adapter.session,'request',return_value=response):
        with pytest.raises(ChatworkAPIError):adapter.get_recent_messages('r')


def test_api_host_origin_csrf_and_secret_redaction(tmp_path):
    from src.app.server import create_app
    app=create_app(str(tmp_path));client=app.test_client()
    key='FAKE-API-KEY-AUDIT'
    app.extensions['services']['config'].set('chatwork_api_key',key)
    html=client.get('/').get_data(as_text=True)
    token=re.search('name="csrf-token" content="([^"]+)"',html)[1]
    assert client.get('/api/config',headers={'Host':'evil.example'}).status_code==403
    assert client.get('/api/config',headers={'Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/sync/run',json={}).status_code==403
    result=client.post('/api/export/create-session',json={},headers={'X-CSRF-Token':token})
    assert result.status_code==400
    assert result.json['operation_id'].startswith('REQ-')
    assert key not in client.get('/api/config').get_data(as_text=True)
    assert key not in client.get('/api/history').get_data(as_text=True)
    assert client.get('/api/config').headers.get('Access-Control-Allow-Origin') is None


def test_four_navigation_items_and_review_controls(tmp_path):
    from src.app.server import create_app
    html=create_app(str(tmp_path)).test_client().get('/').get_data(as_text=True)
    from html.parser import HTMLParser
    class Navigation(HTMLParser):
        def __init__(self):
            super().__init__(); self.sections=[]; self.controls={}
        def handle_starttag(self,tag,attrs):
            attributes=dict(attrs)
            if tag=='button' and 'nav-item' in attributes.get('class','').split():
                self.sections.append(attributes.get('data-section'))
            if attributes.get('id'):
                self.controls[attributes['id']] = (tag, attributes)
    navigation=Navigation();navigation.feed(html)
    assert sorted(navigation.sections) == ['export','history','settings','sync']
    assert navigation.controls['reviewDialog'][0] == 'dialog'
    assert navigation.controls['reviewForm'][0] == 'form'
    assert navigation.controls['confirmReview'][0] == 'button'
    assert navigation.controls['excludeReview'][1]['type'] == 'button'
    assert 'required' in navigation.controls['editName'][1]
    assert 'sourceEvidence' in navigation.controls
    assert 'Nhân viên</button>' not in html


