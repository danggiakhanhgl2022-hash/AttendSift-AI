"""Regression coverage: Excel is published directly to user's Downloads."""
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.app import paths
from src.models.database import (Database, ConfigRepository, MessageRepository,
                                 ExportSessionRepository, ActionEventRepository)
from src.services.export_service import ExportService, ExportServiceError


@pytest.fixture
def approved_session(tmp_path, monkeypatch):
    monkeypatch.setattr('src.utils.security.dpapi', lambda data, decrypt=False: data)
    root = tmp_path / 'portable'
    root.mkdir()
    db = Database(str(root / 'data' / 'chamcong.db'))
    config = ConfigRepository(db)
    config.set('chatwork_room_id', 'test-room')
    config.set('ai_api_key', 'test-only-key')
    messages = MessageRepository(db)
    messages.save_messages_batch([{'message_id': 'm1', 'room_id': 'test-room', 'account_id': 1,
                                   'name': 'Thư', 'body': 'Thư OT 4h ngày 8/10',
                                   'send_time': '2026-10-08T18:00:00+07:00'}])
    service = ExportService(db, config, messages, ExportSessionRepository(db),
                            ActionEventRepository(db), str(root))
    sid = service.create_session(10, 2026, True)['session_id']
    event = dict(person_id='th', employee_name='Thư', identity_evidence='Thư',
                 identity_uncertain=False, event_date='2026-10-08', event_type='Tăng ca',
                 event_subtype=None, reason='Tăng ca', hours_compensation='Không áp dụng',
                 minutes_not_compensated=0, minutes_compensated=0, ot_minutes=240,
                 ot_used_minutes=0, ot_credit_date=None, leave_days=None, start_time=None,
                 end_time=None, source_message_ids=['m1'], confidence=0.99,
                 needs_review=False, review_reason=None)
    adapter = Mock()
    adapter.analyze_attendance.return_value = [event]
    with patch('src.services.export_service.create_ai_adapter', return_value=adapter):
        service.analyze(sid)
    return service, sid, tmp_path


def test_publish_to_downloads_and_preserve_session_history(approved_session):
    service, sid, tmp_path = approved_session
    result = service.export_to_excel(sid)
    published = Path(result['saved_to'])
    archive = Path(result['file_path'])
    assert published == tmp_path / 'Downloads' / 'Cham_cong_10_2026.xlsx'
    assert published.is_file() and archive.is_file()
    assert published.read_bytes() == archive.read_bytes()
    assert not (Path(service.app_path) / 'outputs' / published.name).exists()
    assert service.session_file(service.session_repo.get_session(sid)) == archive
    with service.db._get_connection() as conn:
        stored_hash = conn.execute('SELECT file_hash FROM export_sessions WHERE session_id=?', (sid,)).fetchone()[0]
    assert stored_hash == hashlib.sha256(published.read_bytes()).hexdigest()


def test_existing_downloads_file_needs_permission_to_overwrite(approved_session):
    service, sid, tmp_path = approved_session
    folder = tmp_path / 'Downloads'
    folder.mkdir()
    file = folder / 'Cham_cong_10_2026.xlsx'
    file.write_bytes(b'keep original')
    with pytest.raises(ExportServiceError, match='ghi đè'):
        service.export_to_excel(sid)
    assert file.read_bytes() == b'keep original'
    result = service.export_to_excel(sid, overwrite=True)
    assert file.read_bytes() == Path(result['file_path']).read_bytes()


def test_downloads_resolution_for_regular_home(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, 'platform', 'linux')
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    assert paths.user_downloads_dir() == tmp_path / 'Downloads'


def test_windows_downloads_fallback_to_user_profile(monkeypatch, tmp_path):
    monkeypatch.setattr(paths.sys, 'platform', 'win32')
    monkeypatch.setenv('USERPROFILE', str(tmp_path / 'different user'))
    assert paths.user_downloads_dir() == tmp_path / 'different user' / 'Downloads'


def test_locked_downloads_file_is_not_damaged(approved_session):
    service, sid, tmp_path = approved_session
    folder = tmp_path / 'Downloads'
    folder.mkdir()
    file = folder / 'Cham_cong_10_2026.xlsx'
    file.write_bytes(b'locked-file')
    import os
    original = os.replace

    def simulate_excel_lock(source, destination):
        if Path(destination) == file:
            raise PermissionError('Excel is holding the file open')
        return original(source, destination)

    with patch('src.services.export_service.os.replace', side_effect=simulate_excel_lock):
        with pytest.raises(ExportServiceError, match='Downloads'):
            service.export_to_excel(sid, overwrite=True)
    assert file.read_bytes() == b'locked-file'
    assert service.session_repo.get_session(sid)['status'] == 'ready'


def test_downloads_output_is_always_the_four_sheet_attendance_workbook(approved_session):
    """A TinNhan_ one-sheet dump must never become the primary Downloads output."""
    from zipfile import ZipFile
    from xml.etree import ElementTree
    service, sid, _ = approved_session
    result = service.export_to_excel(sid)
    path = Path(result['saved_to'])
    assert path.name == 'Cham_cong_10_2026.xlsx'
    with ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read('xl/workbook.xml'))
    namespace = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    names = [elem.attrib['name'] for elem in root.findall(f'{namespace}sheets/{namespace}sheet')]
    assert names == ['1_TIN_NHAN_GOC', '2_CHAM_CONG', '3_TONG_KET', '4_CAN_KIEM_TRA']
    assert 'Tin nhan' not in names
