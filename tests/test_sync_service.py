# -*- coding: utf-8 -*-
"""
Tests for sync service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.services.sync_service import SyncService, SyncServiceError
from src.models.database import (
    Database, MessageRepository, ConfigRepository,
    SyncHistoryRepository, ActionEventRepository
)


class TestSyncService:
    """Test sync service"""

    @pytest.fixture
    def sync_service(self, temp_db, tmp_path):
        """Create sync service instance"""
        return SyncService(
            db=temp_db,
            config_repo=ConfigRepository(temp_db),
            message_repo=MessageRepository(temp_db),
            sync_repo=SyncHistoryRepository(temp_db),
            action_repo=ActionEventRepository(temp_db),
            app_path=str(tmp_path)
        )

    def test_sync_requires_api_key(self, sync_service):
        """Test that sync fails without API key configured"""
        with pytest.raises(SyncServiceError) as exc:
            sync_service.sync()
        assert "not configured" in str(exc.value)

    def test_sync_requires_room(self, sync_service):
        """Test that sync fails without room configured"""
        sync_service.config_repo.set('chatwork_api_key', 'test_key')

        with pytest.raises(SyncServiceError) as exc:
            sync_service.sync()
        assert "Room" in str(exc.value) or "room" in str(exc.value)

    @patch('src.services.sync_service.ChatworkAdapter')
    def test_sync_success(self, mock_adapter_class, sync_service):
        """Test successful sync"""
        # Configure
        sync_service.config_repo.set('chatwork_api_key', 'test_key')
        sync_service.config_repo.set('chatwork_room_id', 'ROOM123')

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.get_recent_messages.return_value = [
            {
                'message_id': 'MSG001',
                'room_id': 'ROOM123',
                'account_id': 1,
                'name': 'Test User',
                'body': 'Test message',
                'send_time': '2026-09-01T10:00:00Z'
            }
        ]
        mock_adapter.normalize_message.side_effect = lambda m: {
            'message_id': m['message_id'],
            'room_id': m['room_id'],
            'account_id': m['account_id'],
            'name': m['name'],
            'body': m['body'],
            'send_time': m['send_time']
        }
        mock_adapter_class.return_value = mock_adapter

        result = sync_service.sync(source='manual')

        assert result['success'] == True
        assert result['messages_new'] == 1
        assert 'operation_id' in result

    def test_get_status_returns_configured_values(self, sync_service):
        """Test get_status returns correct values"""
        sync_service.config_repo.set('chatwork_room_id', 'ROOM123')
        sync_service.config_repo.set('chatwork_room_name', 'Test Room')
        sync_service.config_repo.set('sync_hour', 14)
        sync_service.config_repo.set('sync_minute', 30)

        status = sync_service.get_status()

        assert status['room_id'] == 'ROOM123'
        assert status['room_name'] == 'Test Room'
        assert status['sync_hour'] == 14
        assert status['sync_minute'] == 30

    def test_default_sync_time_is_13_00(self, sync_service):
        """Test that default sync time is 13:00"""
        status = sync_service.get_status()

        assert status['sync_hour'] == 13
        assert status['sync_minute'] == 0


class TestSyncConcurrency:
    """Test sync concurrency handling"""

    @pytest.fixture
    def sync_service(self, temp_db, tmp_path):
        """Create sync service instance"""
        return SyncService(
            db=temp_db,
            config_repo=ConfigRepository(temp_db),
            message_repo=MessageRepository(temp_db),
            sync_repo=SyncHistoryRepository(temp_db),
            action_repo=ActionEventRepository(temp_db),
            app_path=str(tmp_path)
        )

    def test_prevents_concurrent_sync(self, sync_service, tmp_path):
        """Test that concurrent syncs are prevented"""
        # Configure
        sync_service.config_repo.set('chatwork_api_key', 'test_key')
        sync_service.config_repo.set('chatwork_room_id', 'ROOM123')

        # Mock adapter to be slow
        with patch('src.services.sync_service.ChatworkAdapter') as mock_class:
            mock_adapter = MagicMock()
            import threading
            from concurrent.futures import ThreadPoolExecutor
            from src.utils.locking import BusyError
            started,release=threading.Event(),threading.Event()
            def slow(*args,**kwargs):
                started.set()
                assert release.wait(5)
                return []
            mock_adapter.get_recent_messages.side_effect = slow
            mock_adapter.normalize_message.side_effect = lambda m: m
            mock_class.return_value = mock_adapter

            # First sync should succeed
            sync_service.app_path = str(tmp_path)

            with ThreadPoolExecutor(max_workers=1) as pool:
                first=pool.submit(sync_service.sync)
                assert started.wait(5)
                try:
                    with pytest.raises(BusyError):sync_service.sync()
                finally:release.set()
                assert first.result(timeout=5)['success']
            assert mock_adapter.get_recent_messages.call_count==1


import time  # For the test
