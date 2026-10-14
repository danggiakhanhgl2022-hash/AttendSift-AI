from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.app import launcher
from src.models.database import ConfigRepository, MessageRepository, SyncHistoryRepository, ActionEventRepository
from src.services.sync_service import SyncService, SyncServiceError
from src.scheduler.timing import TZ, due_slot
from src.utils.locking import BusyError


def test_recover_yesterday_before_today_schedule_and_retry_after_offline(temp_db,tmp_path):
    config=ConfigRepository(temp_db);messages=MessageRepository(temp_db)
    config.set('chatwork_api_key','FAKE-RECOVERY-KEY');config.set('chatwork_room_id','r')
    config.set('sync_hour',14);config.set('sync_minute',30)
    config.set('schedule_enabled',True)
    config.set('schedule_effective_from','2026-09-01T14:30:00+07:00')
    config.set('last_successful_sync:r','2026-09-28T14:31:00+07:00')
    service=SyncService(temp_db,config,messages,SyncHistoryRepository(temp_db),ActionEventRepository(temp_db),str(tmp_path))
    now=TZ.localize(datetime(2026,9,30,8,0))
    assert due_slot({'hour':14,'minute':30},config.get('last_successful_sync:r'),now).startswith('2026-09-29T14:30')
    adapter=Mock();adapter.get_recent_messages.side_effect=[RuntimeError('offline'),[
        {'message_id':str(i),'room_id':'r','body':'Invented source', 'name':'Invented sender',
         'send_time':'2026-09-29T15:00:00+07:00'} for i in range(75)]]
    adapter.normalize_message.side_effect=lambda message:message
    with patch('src.scheduler.timing.datetime',wraps=datetime) as clock, patch('src.services.sync_service.datetime',wraps=datetime) as sync_clock, patch.object(service,'_get_chatwork_adapter',return_value=adapter):
        clock.now.return_value=now;sync_clock.now.return_value=now
        import pytest
        with pytest.raises(SyncServiceError):service.catch_up('scheduled')
        assert config.get('last_successful_sync:r')=='2026-09-28T14:31:00+07:00'
        assert service.catch_up('scheduled')['messages_new']==75
        assert len(messages.get_by_room('r'))==75
        assert service.catch_up('catchup')['skipped']
        assert adapter.get_recent_messages.call_count==2


def test_background_sync_exit_code_requests_windows_retry(tmp_path):
    sync=Mock()
    app=SimpleNamespace(extensions={'services':{'sync':sync}})
    for error in [BusyError('busy'),RuntimeError('offline')]:
        sync.catch_up.side_effect=error
        with patch.object(launcher,'APP_PATH',str(tmp_path)),patch.object(launcher,'create_app',return_value=app),patch('sys.argv',['ChamCong.exe','--sync']),patch('logging.basicConfig'):
            assert launcher.main()==1
    sync.catch_up.side_effect=None;sync.catch_up.return_value={'skipped':True}
    with patch.object(launcher,'APP_PATH',str(tmp_path)),patch.object(launcher,'create_app',return_value=app),patch('sys.argv',['ChamCong.exe','--sync']),patch('logging.basicConfig'):
        assert launcher.main()==0


def test_next_day_login_collects_after_yesterdays_success_then_keeps_daily_time(temp_db,tmp_path):
    config=ConfigRepository(temp_db);messages=MessageRepository(temp_db)
    config.set('chatwork_api_key','FAKE-LOGIN-KEY');config.set('chatwork_room_id','r')
    config.set('sync_hour',14);config.set('sync_minute',30)
    config.set('schedule_enabled',True)
    config.set('schedule_effective_from','2026-09-01T14:30:00+07:00')
    config.set('last_successful_sync:r','2026-09-29T14:31:00+07:00')
    service=SyncService(temp_db,config,messages,SyncHistoryRepository(temp_db),ActionEventRepository(temp_db),str(tmp_path))
    adapter=Mock();adapter.get_recent_messages.return_value=[{'message_id':'late-yesterday','room_id':'r',
         'name':'Invented sender','body':'Source after yesterday schedule','send_time':'2026-09-29T18:00:00+07:00'}]
    adapter.normalize_message.side_effect=lambda m:m
    with patch('src.scheduler.timing.datetime',wraps=datetime) as clock,patch('src.services.sync_service.datetime',wraps=datetime) as sync_clock,patch.object(service,'_get_chatwork_adapter',return_value=adapter):
        clock.now.return_value=sync_clock.now.return_value=TZ.localize(datetime(2026,9,30,8,0))
        assert service.catch_up('scheduled')['messages_new']==1
        assert config.get('completed_slot:r')=='catchup:2026-09-30'
        assert service.catch_up('scheduled')['skipped']
        clock.now.return_value=sync_clock.now.return_value=TZ.localize(datetime(2026,9,30,14,30))
        assert service.catch_up('scheduled')['messages_unchanged']==1
        assert config.get('completed_slot:r').startswith('2026-09-30T14:30')
        assert len(messages.get_by_room('r'))==1


def test_disabled_schedule_never_reads_credentials_or_contacts_api(temp_db,tmp_path):
    config=ConfigRepository(temp_db)
    service=SyncService(temp_db,config,MessageRepository(temp_db),SyncHistoryRepository(temp_db),ActionEventRepository(temp_db),str(tmp_path))
    with patch.object(config,'get_chatwork_config',side_effect=AssertionError('disabled background must not read keys')):
        assert service.catch_up('scheduled')['skipped']
        assert service.catch_up('catchup')['skipped']
