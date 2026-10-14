# -*- coding: utf-8 -*-
"""
Tests for database models
"""
import pytest
from datetime import datetime
import pytz

from src.models.database import (
    Database, MessageRepository, ConfigRepository,
    SyncHistoryRepository, ExportSessionRepository, ActionEventRepository
)

Vietnam_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


class TestDatabase:
    """Test database initialization"""

    def test_init_creates_tables(self, temp_db):
        """Test that database creates all required tables"""
        conn = temp_db._get_connection()
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = [
            'messages', 'message_versions', 'sync_history', 'config',
            'export_sessions', 'ai_results', 'corrections', 'action_events'
        ]

        for table in required_tables:
            assert table in tables, f"Table {table} not found"

        conn.close()

    def test_compute_hash(self, temp_db):
        """Test hash computation"""
        hash1 = temp_db.compute_hash("test content")
        hash2 = temp_db.compute_hash("test content")
        hash3 = temp_db.compute_hash("different content")

        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 64  # SHA256 produces 64 character hex string


class TestMessageRepository:
    """Test message repository operations"""

    def test_save_new_message(self, temp_db, sample_messages):
        """Test saving a new message"""
        repo = MessageRepository(temp_db)

        is_new, is_updated = repo.save_message(
            message_id=sample_messages[0]['message_id'],
            room_id=sample_messages[0]['room_id'],
            account_id=sample_messages[0]['account_id'],
            name=sample_messages[0]['name'],
            body=sample_messages[0]['body'],
            send_time=sample_messages[0]['send_time']
        )

        assert is_new == True
        assert is_updated == False

    def test_save_duplicate_message(self, temp_db, sample_messages):
        """Test saving a duplicate message returns unchanged"""
        repo = MessageRepository(temp_db)

        # First save
        repo.save_message(
            message_id=sample_messages[0]['message_id'],
            room_id=sample_messages[0]['room_id'],
            account_id=sample_messages[0]['account_id'],
            name=sample_messages[0]['name'],
            body=sample_messages[0]['body'],
            send_time=sample_messages[0]['send_time']
        )

        # Second save (duplicate)
        is_new, is_updated = repo.save_message(
            message_id=sample_messages[0]['message_id'],
            room_id=sample_messages[0]['room_id'],
            account_id=sample_messages[0]['account_id'],
            name=sample_messages[0]['name'],
            body=sample_messages[0]['body'],
            send_time=sample_messages[0]['send_time']
        )

        assert is_new == False
        assert is_updated == False

    def test_save_edited_message(self, temp_db, sample_messages):
        """Test saving an edited message"""
        repo = MessageRepository(temp_db)

        # First save
        repo.save_message(
            message_id=sample_messages[0]['message_id'],
            room_id=sample_messages[0]['room_id'],
            account_id=sample_messages[0]['account_id'],
            name=sample_messages[0]['name'],
            body=sample_messages[0]['body'],
            send_time=sample_messages[0]['send_time']
        )

        # Edit and save again
        is_new, is_updated = repo.save_message(
            message_id=sample_messages[0]['message_id'],
            room_id=sample_messages[0]['room_id'],
            account_id=sample_messages[0]['account_id'],
            name=sample_messages[0]['name'],
            body="Edited content",
            send_time=sample_messages[0]['send_time']
        )

        assert is_new == False
        assert is_updated == True

    def test_save_batch(self, temp_db, sample_messages):
        """Test batch saving messages"""
        repo = MessageRepository(temp_db)

        new_count, updated_count, unchanged_count = repo.save_messages_batch(sample_messages)

        assert new_count == 3
        assert updated_count == 0
        assert unchanged_count == 0

    def test_get_by_room(self, temp_db, sample_messages):
        """Test getting messages by room"""
        repo = MessageRepository(temp_db)
        repo.save_messages_batch(sample_messages)

        messages = repo.get_by_room('ROOM123')
        assert len(messages) == 3

        # Non-existent room
        messages = repo.get_by_room('NONEXISTENT')
        assert len(messages) == 0


class TestConfigRepository:
    """Test configuration repository"""

    def test_get_set_value(self, temp_db):
        """Test getting and setting config values"""
        repo = ConfigRepository(temp_db)

        repo.set('test_key', 'test_value')
        assert repo.get('test_key') == 'test_value'

    def test_get_default_value(self, temp_db):
        """Test getting non-existent key returns default"""
        repo = ConfigRepository(temp_db)
        assert repo.get('nonexistent', 'default') == 'default'

    def test_get_sync_schedule(self, temp_db):
        """Test getting sync schedule"""
        repo = ConfigRepository(temp_db)

        schedule = repo.get_sync_schedule()

        assert schedule['hour'] == 13  # Default
        assert schedule['minute'] == 0  # Default
        assert schedule['timezone'] == 'Asia/Ho_Chi_Minh'

    def test_get_chatwork_config(self, temp_db):
        """Test getting Chatwork config"""
        repo = ConfigRepository(temp_db)

        config = repo.get_chatwork_config()

        assert 'api_key' in config
        assert 'room_id' in config
        assert 'room_name' in config


class TestSyncHistoryRepository:
    """Test sync history repository"""

    def test_save_and_get_sync(self, temp_db):
        """Test saving and retrieving sync records"""
        repo = SyncHistoryRepository(temp_db)

        sync_time = datetime.now(Vietnam_TZ).isoformat()
        repo.save_sync(
            sync_time=sync_time,
            source='manual',
            room_id='ROOM123',
            status='success',
            messages_new=10,
            messages_updated=2,
            messages_unchanged=5
        )

        recent = repo.get_recent(limit=10)
        assert len(recent) == 1
        assert recent[0]['messages_new'] == 10

    def test_get_last_successful(self, temp_db):
        """Test getting last successful sync"""
        repo = SyncHistoryRepository(temp_db)

        # Failed sync
        repo.save_sync(
            sync_time=datetime.now(Vietnam_TZ).isoformat(),
            source='manual',
            room_id='ROOM123',
            status='failed',
            messages_new=0,
            messages_updated=0,
            messages_unchanged=0,
            error_message='Test error'
        )

        # Successful sync
        repo.save_sync(
            sync_time=datetime.now(Vietnam_TZ).isoformat(),
            source='manual',
            room_id='ROOM123',
            status='success',
            messages_new=5,
            messages_updated=1,
            messages_unchanged=10
        )

        last = repo.get_last_successful()
        assert last is not None
        assert last['status'] == 'success'
        assert last['messages_new'] == 5


class TestExportSessionRepository:
    """Test export session repository"""

    def test_create_session(self, temp_db):
        """Test creating an export session"""
        repo = ExportSessionRepository(temp_db)

        session_id = repo.create_session(
            session_id='SES-TEST123',
            month=9,
            year=2026,
            ai_provider='anthropic',
            ai_model='claude-sonnet'
        )

        assert session_id == 'SES-TEST123'

        session = repo.get_session('SES-TEST123')
        assert session is not None
        assert session['month'] == 9
        assert session['year'] == 2026
        assert session['status'] == 'analyzing'

    def test_get_session_by_month(self, temp_db):
        """Test getting session by month/year"""
        repo = ExportSessionRepository(temp_db)

        repo.create_session('SES-TEST1', 9, 2026)
        repo.create_session('SES-TEST2', 10, 2026)

        session = repo.get_session_by_month(9, 2026)
        assert session['session_id'] == 'SES-TEST1'

    def test_save_results(self, temp_db, sample_ai_results):
        """Test saving AI results"""
        repo = ExportSessionRepository(temp_db)
        repo.create_session('SES-TEST', 9, 2026)

        repo.save_results('SES-TEST', sample_ai_results)

        results = repo.get_results('SES-TEST')
        assert len(results) == 4


class TestActionEventRepository:
    """Test action event repository"""

    def test_log_event(self, temp_db):
        """Test logging an action event"""
        repo = ActionEventRepository(temp_db)

        repo.log_event(
            operation_id='OP-TEST1',
            action_type='sync',
            source='manual',
            status='success',
            summary='Test sync'
        )

        events = repo.get_events(limit=10)
        assert len(events) == 1
        assert events[0]['action_type'] == 'sync'

    def test_get_by_session(self, temp_db):
        """Test getting events by session"""
        repo = ActionEventRepository(temp_db)

        repo.log_event(
            operation_id='OP-1',
            session_id='SES-TEST',
            action_type='create_session',
            source='user',
            status='created'
        )
        repo.log_event(
            operation_id='OP-2',
            session_id='SES-TEST',
            action_type='analyze',
            source='ai',
            status='success'
        )

        events = repo.get_by_session('SES-TEST')
        assert len(events) == 2
