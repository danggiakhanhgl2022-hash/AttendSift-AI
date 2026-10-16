"""Regression: Vercel Cron uses a rotating production deployment hostname."""
from contextlib import contextmanager
from cloud.app import create_app
from cloud.security import PASSWORD_HASHER
from tests.test_cloud_web import MemoryRepository

SECRET = 'synthetic-cron-secret-32-chars-minimum-123456'

class Repo(MemoryRepository):
    def purge_expired(self):
        self.purge_calls = getattr(self, "purge_calls", 0) + 1
        return {"deleted": {}, "cutoff": "synthetic"}

    @contextmanager
    def lease(self, resource, seconds=120):
        yield 'synthetic-lease-token'

    def save_messages(self, room_id, messages, owner):
        return {'inserted': len(messages), 'updated': 0, 'unchanged': 0}

class Chatwork:
    def __init__(self, key):
        assert key == 'synthetic-chatwork-token'

    def get_recent_messages(self, room_id):
        return []


def test_cron_deployment_host_requires_strong_bearer_token():
    repo = Repo()
    app = create_app(repository=repo, chatwork_factory=Chatwork, config={
        'CHAMCONG_SESSION_SECRET': 'synthetic-local-session-secret-123456789',
        'CHAMCONG_ADMIN_PASSWORD_HASH': PASSWORD_HASHER.hash('synthetic-password'),
        'CHAMCONG_ALLOWED_HOSTS': 'attend-sift-ai.vercel.app',
        'CRON_SECRET': SECRET,
        'CHATWORK_ROOM_ID': '123',
        'CHATWORK_API_KEY': 'synthetic-chatwork-token',
        'CHAMCONG_INSECURE_LOCAL': '1',
    })
    app.config['TESTING'] = True
    client = app.test_client()
    deployment = 'attend-sift-new-deployment.example.vercel.app'
    path = '/api/cron/sync'
    correct_header = {'Host': deployment, 'Authorization': 'Bearer ' + SECRET}
    assert client.get(path, headers=correct_header).status_code == 200
    assert client.get(path, headers={'Host': deployment}).status_code == 403
    assert client.get(path, headers={'Host': deployment,
            'Authorization': 'Bearer wrong'}).status_code == 403
    assert client.get(path, headers={'Host': 'attend-sift-ai.vercel.app'}).status_code == 401
    assert client.get('/api/config', headers=correct_header).status_code == 403

    assert repo.purge_calls == 1, "Only an authorized cron may delete data"
