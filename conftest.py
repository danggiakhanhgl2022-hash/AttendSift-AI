# -*- coding: utf-8 -*-
"""
Pytest configuration and fixtures
"""
import pytest
import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = Database(path)
    yield db
    os.unlink(path)


@pytest.fixture
def sample_messages():
    """Sample Chatwork messages for testing"""
    return [
        {
            'message_id': 'MSG001',
            'room_id': 'ROOM123',
            'account_id': 1,
            'name': 'Nguyễn Văn A',
            'body': 'Em xin phép đi trễ 30 phút có làm bù',
            'send_time': '2026-09-01T08:00:00+07:00'
        },
        {
            'message_id': 'MSG002',
            'room_id': 'ROOM123',
            'account_id': 2,
            'name': 'Trần Thị B',
            'body': 'Team X đã tăng ca:\nA tăng ca 2h\nB tăng ca 1h30',
            'send_time': '2026-09-01T18:00:00+07:00'
        },
        {
            'message_id': 'MSG003',
            'room_id': 'ROOM123',
            'account_id': 3,
            'name': 'Lê Văn C',
            'body': 'Em xin phép nghỉ ngày mai (phép năm)\nLý do: Việc cá nhân',
            'send_time': '2026-09-01T17:00:00+07:00'
        }
    ]


@pytest.fixture
def sample_ai_results():
    """Sample AI analysis results for testing"""
    return [
        {
            'event_id': 'EVT001',
            'source_id': 'MSG001',
            'employee_name': 'Nguyễn Văn A',
            'display_name': 'Nguyễn Văn A',
            'event_date': '2026-09-01',
            'event_type': 'Đi trễ',
            'event_subtype': None,
            'reason': 'Việc cá nhân',
            'hours_compensation': 'Có',
            'is_compensated': True,
            'minutes_not_compensated': 0,
            'minutes_compensated': 30,
            'source_message_ids': ['MSG001'],
            'confidence': 0.95,
            'needs_review': False,
            'review_reason': None
        },
        {
            'event_id': 'EVT002',
            'source_id': 'MSG002',
            'employee_name': 'A',
            'display_name': 'Nguyễn Văn A',
            'event_date': '2026-09-01',
            'event_type': 'Tăng ca',
            'event_subtype': None,
            'reason': 'Team X',
            'hours_compensation': 'Không',
            'is_compensated': False,
            'minutes_not_compensated': 0,
            'minutes_compensated': 120,
            'source_message_ids': ['MSG002'],
            'confidence': 0.90,
            'needs_review': False,
            'review_reason': None
        },
        {
            'event_id': 'EVT003',
            'source_id': 'MSG002',
            'employee_name': 'B',
            'display_name': 'Trần Thị B',
            'event_date': '2026-09-01',
            'event_type': 'Tăng ca',
            'event_subtype': None,
            'reason': 'Team X',
            'hours_compensation': 'Không',
            'is_compensated': False,
            'minutes_not_compensated': 0,
            'minutes_compensated': 90,
            'source_message_ids': ['MSG002'],
            'confidence': 0.85,
            'needs_review': True,
            'review_reason': 'Tên viết tắt, cần xác nhận'
        },
        {
            'event_id': 'EVT004',
            'source_id': 'MSG003',
            'employee_name': 'Lê Văn C',
            'display_name': 'Lê Văn C',
            'event_date': '2026-09-02',
            'event_type': 'Nghỉ',
            'event_subtype': 'Phép năm',
            'reason': 'Việc cá nhân',
            'hours_compensation': 'Không',
            'is_compensated': False,
            'minutes_not_compensated': 0,
            'minutes_compensated': 0,
            'source_message_ids': ['MSG003'],
            'confidence': 0.98,
            'needs_review': False,
            'review_reason': None
        }
    ]


@pytest.fixture(autouse=True)
def isolate_user_downloads(monkeypatch, tmp_path):
    """Never write regression-test Excel files to the real user's Downloads."""
    monkeypatch.setattr('src.services.export_service.user_downloads_dir', lambda: tmp_path / 'Downloads')
