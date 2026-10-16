"""Run once against a provisioned Neon branch, never automatically on public requests."""
import os
from .repository import PostgresRepository

if __name__ == '__main__':
    PostgresRepository(os.environ.get('DATABASE_URL')).migrate()
    print('Cloud schema migrated successfully. Connection string withheld.')
