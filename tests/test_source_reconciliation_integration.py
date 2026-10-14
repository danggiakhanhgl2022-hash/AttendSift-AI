"""SQLite + export service regression, without Windows DPAPI or real AI key."""
from unittest.mock import Mock, patch

from src.models.database import Database, ConfigRepository, MessageRepository, ExportSessionRepository, ActionEventRepository
from src.services.export_service import ExportService
from tests.test_source_reconciliation import row


def test_analysis_persists_source_repairs_and_keeps_original(tmp_path):
    db = Database(str(tmp_path / 'data.db'))
    config = ConfigRepository(db)
    config.set('chatwork_room_id', 'room')
    messages = MessageRepository(db)
    messages.save_messages_batch([{
        'message_id':'u1', 'room_id':'room', 'account_id':77,
        'name':'ウェン (Phạm Gia Uyên)',
        'body':'Em xin phép về sớm 30 phút không làm bù (./.)\nEm xin cảm ơn!',
        'send_time':'2026-10-14T11:02:37+07:00'
    }])
    service = ExportService(db, config, messages, ExportSessionRepository(db), ActionEventRepository(db), str(tmp_path))
    fake_config = {'provider':'custom','model':'fake','base_url':'https://example.invalid/v1','api_key':'test-not-a-real-key'}
    fake_ai = Mock()
    fake_ai.analyze_attendance.return_value = [row('u1', 'Bùi Ngân Hoa', '2026-10-13', 'Về sớm', identity_evidence='Hoa')]
    with patch.object(config,'get_ai_provider',return_value=fake_config), patch('src.services.export_service.create_ai_adapter',return_value=fake_ai):
        session_id=service.create_session(10,2026,accept_risk=True)['session_id']
        answer=service.analyze(session_id)
    results=service.get_results(session_id)
    assert answer['status']=='review' and len(results)==1
    result=results[0]
    assert result['employee_name']=='Phạm Gia Uyên'
    assert result['event_date']=='2026-10-14'
    assert result['review_state']=='pending'
    assert result['ai_raw_output']['employee_name']=='Bùi Ngân Hoa'
    assert not result['validation_errors']


def test_annual_leave_is_saved_without_payroll_rows(tmp_path):
    db = Database(str(tmp_path / 'data.db'))
    config = ConfigRepository(db)
    config.set('chatwork_room_id', 'room')
    messages = MessageRepository(db)
    original = 'Em xin phép nghỉ ngày thứ 5,6 ngày 1-2/10( phép năm)'
    messages.save_messages_batch([{
        'message_id':'leave', 'room_id':'room', 'account_id':79,
        'name':'クイン (Đặng Như Quỳnh)', 'body':original,
        'send_time':'2026-09-30T23:41:57+07:00'
    }])
    service = ExportService(db, config, messages, ExportSessionRepository(db), ActionEventRepository(db), str(tmp_path))
    fake_config = {'provider':'custom','model':'fake','base_url':'https://example.invalid/v1','api_key':'test-not-a-real-key'}
    fake_ai = Mock()
    fake_ai.analyze_attendance.return_value = [row('leave', 'Đặng Như Quỳnh', '2026-10-01', 'Nghỉ')]
    with patch.object(config,'get_ai_provider',return_value=fake_config), patch('src.services.export_service.create_ai_adapter',return_value=fake_ai):
        session_id = service.create_session(10,2026,accept_risk=True)['session_id']
        assert service.analyze(session_id)['status'] == 'ready'
    results = service.get_results(session_id, include_excluded=True)
    assert len(results) == 1 and results[0]['is_excluded'] and results[0]['source_only']
    assert service.get_results(session_id) == []
    assert service._session(session_id)['snapshot_data'][0]['body'] == original


def test_wrong_ai_employee_does_not_create_extra_group_payroll_row(tmp_path):
    db = Database(str(tmp_path / 'data.db'))
    config = ConfigRepository(db)
    config.set('chatwork_room_id', 'room')
    messages = MessageRepository(db)
    messages.save_messages_batch([{
        'message_id':'multi', 'room_id':'room', 'account_id':101,
        'name':'Người Báo Hộ',
        'body':'Team DemoBeta: ngày 2/10\nThư OT 2h30\nCẩm OT 2h30\nBảo 30ph đối ứng curious',
        'send_time':'2026-10-03T09:00:00+07:00'
    }])
    service = ExportService(db,config,messages,ExportSessionRepository(db),ActionEventRepository(db),str(tmp_path))
    fake_config = {'provider':'custom','model':'fake','base_url':'https://example.invalid/v1','api_key':'test-only'}
    fake_ai = Mock()
    fake_ai.analyze_attendance.return_value = [row('multi','Nghĩa','2026-10-02','Tăng ca',150)]
    with patch.object(config,'get_ai_provider',return_value=fake_config),patch('src.services.export_service.create_ai_adapter',return_value=fake_ai):
        sid=service.create_session(10,2026,accept_risk=True)['session_id']
        answer=service.analyze(sid)
    rows=service.get_results(sid,include_excluded=True)
    assert answer['status']=='ready'
    assert len(rows)==4
    incorrect=next(r for r in rows if r['employee_name']=='Nghĩa')
    assert incorrect['is_excluded'] and incorrect['ai_raw_output']['employee_name']=='Nghĩa'
    active=[r for r in rows if not r['is_excluded']]
    assert {(r['employee_name'],r['event_date'],r['ot_minutes']) for r in active} == {
        ('Thư','2026-10-02',150),('Cẩm','2026-10-02',150),('Bảo','2026-10-02',30)}
    assert all(r['review_state']=='valid' and not r['validation_errors'] for r in active)


def test_demoalpha_my_ctv_excluded_from_payroll_but_full_group_retained(tmp_path):
    db = Database(str(tmp_path / 'data.db'))
    cfg = ConfigRepository(db)
    cfg.set('chatwork_room_id', 'room')
    repo = MessageRepository(db)
    original_body = ('Team DemoAlpha: ngày 01/10\n'
                     'Tân, Hào, Quỳnh Anh OT 30 phút\n'
                     'An (CTV) OT 30 phút\n'
                     'Hỗ trợ dự án DemoAlpha')
    repo.save_messages_batch([{
        'message_id':'g1', 'room_id':'room', 'account_id':91,
        'name':'Lê Minh Tân', 'body':original_body,
        'send_time':'2026-10-02T09:02:56+07:00'
    }])
    service = ExportService(db, cfg, repo, ExportSessionRepository(db),
                            ActionEventRepository(db), str(tmp_path))
    fake_ai = Mock()
    # The model produces the CTV row despite the explicit source-only policy.
    fake_ai.analyze_attendance.return_value = [row('g1', 'An (CTV)', '2026-10-01', 'Tăng ca', 30)]
    fake_config = {'provider':'custom', 'model':'fake', 'base_url':'https://example.invalid/v1',
                   'api_key':'not-real'}
    with patch.object(cfg, 'get_ai_provider', return_value=fake_config), patch(
        'src.services.export_service.create_ai_adapter', return_value=fake_ai
    ):
        sid = service.create_session(10, 2026, accept_risk=True)['session_id']
        service.analyze(sid)
    results = service.get_results(sid, include_excluded=True)
    assert len(results) == 4
    assert {r['employee_name'] for r in results if not r['is_excluded']} == {
        'Lê Minh Tân','Hào','Quỳnh Anh'}
    assert all(r['ot_minutes'] == 30 for r in results)
    my = next(r for r in results if r['employee_name'] == 'An (CTV)')
    assert my['is_excluded'] and my['source_only']
    assert my['ai_raw_output']['employee_name'] == 'An (CTV)'
    assert not any(r['employee_name'] == 'An (CTV)' for r in service.get_results_for_review(sid))
    assert service._session(sid)['snapshot_data'][0]['body'] == original_body
