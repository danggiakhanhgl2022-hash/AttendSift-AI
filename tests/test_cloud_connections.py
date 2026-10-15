"""Authenticated connection settings survive requests without exposing API keys."""
import copy
import pytest
from cloud.app import create_app
from cloud.security import PASSWORD_HASHER
from cloud.credentials import unseal
from tests.test_cloud_web import MemoryRepository


class SettingsRepository(MemoryRepository):
    def __init__(self):
        super().__init__()
        self.settings = {}

    def get_setting(self, key, default=None):
        return copy.deepcopy(self.settings.get(key, default))

    def set_setting(self, key, value):
        self.settings[key] = copy.deepcopy(value)


class FakeAI:
    def __init__(self, **kwargs):
        self.model = kwargs.get('model') or 'synthetic-model'
        self.key = kwargs['api_key']

    def test_connection(self):
        if self.key == 'rejected-key':
            raise ValueError('Rejected')


class FakeChatwork:
    def __init__(self, key):
        self.key = key

    def get_rooms(self):
        assert self.key == 'synthetic-chatwork-key'
        return [{'room_id':123, 'name':'Synthetic team'}]


@pytest.fixture
def setup():
    repo = SettingsRepository()
    secret = 'synthetic-connection-session-secret-1234567890'
    config = {'CHAMCONG_SESSION_SECRET':secret,
              'CHAMCONG_ADMIN_PASSWORD_HASH':PASSWORD_HASHER.hash('synthetic-password'),
              'CHAMCONG_ALLOWED_HOSTS':'localhost', 'CHAMCONG_INSECURE_LOCAL':'1'}
    app = create_app(repository=repo, config=config, ai_factory=FakeAI, chatwork_factory=FakeChatwork)
    client = app.test_client()
    response = client.post('/login', json={'password':'synthetic-password'})
    headers = {'X-CSRF-Token':response.json['data']['csrf_token']}
    return client, repo, secret, headers, config


def test_ai_key_encrypted_retained_and_not_returned(setup):
    client, repo, secret, headers, config = setup
    data = {'provider':'gemini', 'api_key':'synthetic-gemini-key', 'model':'synthetic-model'}
    assert client.post('/api/config/ai',json=data).status_code == 403
    assert client.post('/api/config/ai',json=data,headers=headers).status_code == 200
    stored = repo.settings['ai_connection']
    assert 'synthetic-gemini-key' not in str(stored)
    assert unseal(stored['encrypted_key'],secret) == 'synthetic-gemini-key'
    assert unseal(stored['encrypted_key'],secret+'rotated') == ''
    assert client.post('/api/config/ai',json={'provider':'gemini','api_key':'','model':'changed-model'},headers=headers).status_code == 200
    response = client.get('/api/config')
    assert response.json['data']['has_ai_key'] is True
    assert response.json['data']['ai_model'] == 'changed-model'
    assert 'synthetic-gemini-key' not in response.get_data(as_text=True)
    assert 'synthetic-gemini-key' not in str(repo.events)
    # A fresh app instance reads the persisted encrypted settings.
    other = create_app(repository=repo,config=config,ai_factory=FakeAI).test_client()
    other.post('/login',json={'password':'synthetic-password'})
    assert other.get('/api/config').json['data']['has_ai_key'] is True


def test_failed_ai_check_does_not_replace_connection(setup):
    client, repo, secret, headers, _ = setup
    data = {'provider':'gemini','api_key':'synthetic-gemini-key'}
    assert client.post('/api/config/ai',json=data,headers=headers).status_code == 200
    before = copy.deepcopy(repo.settings)
    assert client.post('/api/config/ai',json={**data,'api_key':'rejected-key'},headers=headers).status_code == 400
    assert repo.settings == before
    assert client.post('/api/config/ai',json={'provider':'openai','api_key':''},headers=headers).status_code == 400
    assert client.post('/api/config/ai',json={'provider':'custom','api_key':'x'},headers=headers).status_code == 400


def test_chatwork_key_used_by_room_api_and_never_exposed(setup):
    client, repo, secret, headers, _ = setup
    response = client.post('/api/config/chatwork',json={'api_key':'synthetic-chatwork-key'},headers=headers)
    assert response.status_code == 200
    assert 'synthetic-chatwork-key' not in str(repo.settings)
    assert client.get('/api/rooms').json['data'][0]['room_id'] == 123
    assert client.get('/api/config').json['data']['has_chatwork_key'] is True
    assert 'synthetic-chatwork-key' not in client.get('/api/config').get_data(as_text=True)
    anonymous = client.application.test_client()
    assert anonymous.post('/api/config/chatwork',json={'api_key':'x'}).status_code == 401
