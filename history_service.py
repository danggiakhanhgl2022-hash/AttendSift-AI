# -*- coding: utf-8 -*-
"""
History service for viewing action logs
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz

from ..models.database import (
    Database, ActionEventRepository, ExportSessionRepository,
    SyncHistoryRepository
)

Vietnam_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


class HistoryService:
    """Service for viewing action history"""

    def __init__(self, db: Database, action_repo: ActionEventRepository,
                 session_repo: ExportSessionRepository, sync_repo: SyncHistoryRepository):
        self.db = db
        self.action_repo = action_repo
        self.session_repo = session_repo
        self.sync_repo = sync_repo

    def get_events(self, start_time: str = None, end_time: str = None,
                  action_types: List[str] = None, statuses: List[str] = None,
                  limit: int = 100) -> List[Dict]:
        """Get action events with filters"""
        return self.action_repo.get_events(
            start_time=start_time,
            end_time=end_time,
            action_types=action_types,
            statuses=statuses,
            limit=limit
        )

    def get_sync_history(self, limit: int = 50) -> List[Dict]:
        """Get sync history"""
        return self.sync_repo.get_recent(limit=limit)

    def get_export_sessions(self, month: int = None, year: int = None) -> List[Dict]:
        """Get export sessions"""
        if month and year:
            session = self.session_repo.get_session_by_month(month, year)
            return [session] if session else []
        return []

    def get_session_events(self, session_id: str) -> List[Dict]:
        """Get all events for a session"""
        return self.action_repo.get_by_session(session_id)

    def get_corrections(self, session_id: str) -> List[Dict]:
        """Get all corrections for a session"""
        return self.session_repo.get_corrections(session_id)

    def get_event_detail(self, event_id: int) -> Optional[Dict]:
        """Get detailed event info"""
        events = self.action_repo.get_events(limit=1000)
        for event in events:
            if event.get('event_id') == event_id:
                return event
        return None

    def get_dashboard_summary(self) -> Dict:
        """Get dashboard summary for history view"""
        now = datetime.now(Vietnam_TZ)
        week_ago = (now - timedelta(days=7)).isoformat()

        # Get recent events
        recent_events = self.action_repo.get_events(
            start_time=week_ago,
            limit=100
        )

        with self.db._get_connection() as conn:
            counts = conn.execute("""SELECT
                SUM(action_type='sync') AS sync_count,
                SUM(action_type IN ('export','create_session','analyze')) AS export_count,
                SUM(action_type GLOB 'config_*') AS config_count,
                SUM(status='success') AS success_count,
                SUM(status='failed') AS failed_count
                FROM action_events WHERE action_time >= ?""", (week_ago,)).fetchone()
        sync_count, export_count, config_count, success_count, failed_count = (value or 0 for value in counts)

        # Get last sync
        last_sync = self.sync_repo.get_last_successful()

        return {
            'period': '7 ngày gần đây',
            'sync_count': sync_count,
            'export_count': export_count,
            'config_count': config_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'last_sync': last_sync,
            'recent_events': recent_events[:20]
        }
