from datetime import datetime
from unittest.mock import patch

from src.adapters.chatwork_adapter import ChatworkAdapter
from src.models.database import ConfigRepository, ActionEventRepository
from src.services.config_service import ConfigService
from src.services.export_service import ExportService
from src.services.sync_service import SyncService


def test_real_chatwork_message():
    message = ChatworkAdapter('test').normalize_message({
        'message_id': '123', 'room_id': '456', 'send_time': 1791417600,
        'account': {'account_id': 7, 'name': 'Nguyễn Văn A'}, 'body': 'Đi trễ'})
    assert message['account_id'] == 7
    assert message['name'] == 'Nguyễn Văn A'
    assert datetime.fromisoformat(message['send_time']).timestamp() == 1791417600


def test_sync_lock_contends_and_releases(tmp_path):
    first = SyncService(None, None, None, None, None, str(tmp_path))
    second = SyncService(None, None, None, None, None, str(tmp_path))
    assert first._acquire_lock()
    try:
        assert not first._acquire_lock()
        assert not second._acquire_lock()
    finally:
        first._release_lock()
    assert second._acquire_lock()
    second._release_lock()


def test_backup_preserves_wal_and_restores(temp_db, tmp_path):
    repo = ConfigRepository(temp_db)
    service = ConfigService(temp_db, repo, ActionEventRepository(temp_db), str(tmp_path))
    repo.set('test', 'before')
    backup = service.create_backup()['backup_path']
    repo.set('test', 'after')
    # Avoid rotating the backup under test when preserving the current state.
    with patch.object(service, 'create_backup', return_value={'success': True}):
        service.restore_backup(backup)
    assert repo.get('test') == 'before'


def test_month_risk_accepts_timezone():
    service = ExportService(None, None, None, None, None, '.')
    risk = service._verify_data_risk([{'send_time': '2026-09-01T08:00:00+07:00'}], 9, 2026)
    assert risk['target_month_count'] == 1


def test_correction_updates_result(temp_db, sample_ai_results):
    from src.models.database import ExportSessionRepository
    repo = ExportSessionRepository(temp_db)
    repo.create_session('test', 9, 2026)
    repo.save_results('test', sample_ai_results)
    result = repo.get_results('test')[0]
    repo.save_correction(result['result_id'], 'test', 'minutes_compensated', '30', 0)
    assert repo.get_results('test')[0]['minutes_compensated'] == 0


def test_excel_summary_includes_first_row(tmp_path):
    from openpyxl import load_workbook
    from src.utils.excel_export import export_to_excel
    path = str(tmp_path / 'attendance.xlsx')
    export_to_excel([{'employee_name': 'A', 'event_type': 'Tăng ca', 'event_date':'2026-09-05',
                      'ot_minutes': 120, 'hours_compensation': 'Không',
                      'review_reason': 'Giữ ghi chú'}],
                    {'month': 9, 'year': 2026}, path)
    wb = load_workbook(path)
    try:
        detail = wb['2_CHAM_CONG']
        assert detail['V5'].value == 120
        assert detail['W5'].value == '=V5/60'
        assert detail['X5'].value == 'Giữ ghi chú'
        assert '$L$5:' in wb['3_TONG_KET']['C5'].value
    finally:
        wb.close()


def test_webview_uses_supported_window_arguments():
    import inspect
    import pytest
    webview = pytest.importorskip('webview', reason='Optional desktop dependency; exercised by windows-local CI')
    from src.app.launcher import open_webview
    signature = inspect.signature(webview.create_window)
    with patch.object(webview, 'create_window', autospec=True) as create:
        with patch.object(webview, 'start'):
            open_webview(18765)
    signature.bind(**create.call_args.kwargs)
    assert create.call_args.kwargs['min_size'] == (900, 600)
    assert create.call_args.kwargs['url'] == 'http://127.0.0.1:18765'
