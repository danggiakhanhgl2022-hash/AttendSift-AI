"""Synthetic retention boundaries and prevention of re-importing expired data."""
from contextlib import contextmanager
from datetime import datetime
import pytest
from cloud.retention import retention_cutoff
from cloud.repository import PostgresRepository


@pytest.mark.parametrize('now,expected', [
    ('2026-10-15T13:00:00+07:00', '2026-07-15T13:00:00+07:00'),
    ('2026-05-31T13:00:00+07:00', '2026-02-28T13:00:00+07:00'),
    ('2024-05-31T13:00:00+07:00', '2024-02-29T13:00:00+07:00'),
    ('2026-01-01T00:00:00+07:00', '2025-10-01T00:00:00+07:00'),
    ('2026-09-30T18:30:00+00:00', '2026-07-01T01:30:00+07:00'),
])
def test_calendar_cutoff(now, expected):
    assert retention_cutoff(datetime.fromisoformat(now)).isoformat() == expected


def test_sync_does_not_restore_expired_messages(monkeypatch):
    cutoff = datetime.fromisoformat('2026-07-15T13:00:00+07:00')
    monkeypatch.setattr('cloud.repository.retention_cutoff', lambda: cutoff)
    writes = []

    class Result:
        def fetchone(self):
            return None

    class Connection:
        def execute(self, sql, params=None):
            writes.append((sql, params))
            return Result()

    class Repo(PostgresRepository):
        @contextmanager
        def connection(self):
            yield Connection()

        def _assert_lease(self, *args):
            pass

        @staticmethod
        def json(value):
            return value

    messages = [dict(message_id='expired', body='synthetic old message',
                     send_time='2026-07-15T12:59:59+07:00'),
                dict(message_id='boundary', body='synthetic retained message',
                     send_time=cutoff.isoformat())]
    counts = Repo('postgres://synthetic').save_messages('demo', messages, 'owner')
    assert counts['skipped_old'] == 1
    assert counts['added'] == 1
    inserts = [params for sql, params in writes if 'INSERT INTO cc_messages(' in sql]
    assert len(inserts) == 1
    assert inserts[0][1] == 'boundary'
