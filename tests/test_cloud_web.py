"""Cloud-only acceptance tests: synthetic staff, no network or real credentials."""
from io import BytesIO
import openpyxl
import pytest
from cloud.security import PASSWORD_HASHER
from cloud.app import create_app, finalize
from src.utils.excel_export import export_to_excel


class MemoryRepository:
    def __init__(self):
        self.attempts = {}
        self.auth_sessions = {}
        self.now = 10000
        self.events = []

    def login_allowed(self, fingerprint, limit=10):
        self.attempts[fingerprint] = self.attempts.get(fingerprint, 0) + 1
        return self.attempts[fingerprint] <= limit

    def create_auth_session(self, digest, lifetime_seconds):
        self.auth_sessions[digest] = [self.now + lifetime_seconds, self.now]

    def auth_session_valid(self, digest, idle_seconds):
        record = self.auth_sessions.get(digest)
        if not record or record[0] <= self.now or record[1] <= self.now - idle_seconds:
            return False
        record[1] = self.now
        return True

    def revoke_auth_session(self, digest):
        self.auth_sessions.pop(digest, None)

    def ready(self):
        return True

    def log(self, *args, **kwargs):
        self.events.append((args, kwargs))

    def error_summary(self):
        return {'errors_24h': len(self.events)}

    def get_setting(self, key, default=None):
        return default


@pytest.fixture
def client():
    app = create_app(repository=MemoryRepository(), config={
        'CHAMCONG_SESSION_SECRET': 'synthetic-test-session-secret-1234567890',
        'CHAMCONG_ADMIN_PASSWORD_HASH': PASSWORD_HASHER.hash('synthetic-password'),
        'CHAMCONG_ALLOWED_HOSTS': 'localhost', 'CHAMCONG_INSECURE_LOCAL': '1',
        'CHATWORK_ROOM_ID': '12345'})
    app.config['TESTING'] = True
    return app.test_client()


def test_login_required_and_unknown_host_rejected(client):
    assert client.get('/api/config').status_code == 401
    assert client.get('/health', headers={'Host': 'untrusted.example'}).status_code == 403


def test_login_csrf_and_no_secret_exposure(client):
    assert client.post('/login', json={'password': 'wrong'}).status_code == 401
    login = client.post('/login', json={'password': 'synthetic-password'})
    assert login.status_code == 200
    token = login.json['data']['csrf_token']
    assert client.get('/').status_code == 200
    assert client.post('/logout').status_code == 403
    assert client.post('/logout', headers={'X-CSRF-Token': token, 'Origin': 'https://untrusted.example'}).status_code == 403
    assert 'synthetic-password' not in client.get('/api/config').get_data(as_text=True)
    assert client.post('/logout', headers={'X-CSRF-Token': token}).status_code == 200


def test_cloud_group_policy_export_preserves_raw_and_official_alias():
    source = [{'message_id': 'synthetic-1', 'account_id': 1, 'name': 'Người báo hộ',
               'send_time': '2026-10-08T09:00:00+07:00',
               'body': 'Team DemoBeta: ngày 8/10\nBảo OT 1h: đối ứng dự án thử\nCầm OT 1h\nTráng OT 1h\nNy OT 1h\nAn (CTV) OT 1h'}]
    events = finalize([], source, 10, 2026, 'synthetic', {'Bảo': 'Nhân viên thử nghiệm'})
    active = [e for e in events if not e.get('is_excluded')]
    assert len(active) == 4
    assert active[0]['employee_name'] == 'Nhân viên thử nghiệm'
    assert active[0]['ot_minutes'] == 60
    assert active[0]['reason'] == 'đối ứng dự án thử'
    output = BytesIO()
    export_to_excel(events, {'month': 10, 'year': 2026, 'snapshot': source, 'is_draft': True}, output)
    output.seek(0)
    workbook = openpyxl.load_workbook(output)
    assert workbook.worksheets[0]['E5'].value == source[0]['body']
    assert workbook.worksheets[1]['F5'].value == 'Nhân viên thử nghiệm'
    workbook.close()
    output.seek(0)
    cached = openpyxl.load_workbook(output, data_only=True)
    assert cached.worksheets[2]['I5'].value == 60
    assert cached.worksheets[2]['M5'].value == 1
    cached.close()


def test_invalid_alias_configuration_fails_closed():
    with pytest.raises(RuntimeError, match='ALIASES'):
        create_app(repository=MemoryRepository(), config={'CHAMCONG_EMPLOYEE_ALIASES': '[]'})


def test_login_rate_limit_is_shared_and_cannot_spoof_forwarded_ip(client):
    for _ in range(10):
        assert client.post('/login', json={'password': 'wrong'}).status_code == 401
    result = client.post('/login', json={'password': 'synthetic-password'}, headers={'X-Forwarded-For': '203.0.113.99'})
    assert result.status_code == 429
    assert result.headers['Retry-After'] == '900'


def test_idle_session_expires(client):
    assert client.post('/login', json={'password': 'synthetic-password'}).status_code == 200
    client.application.extensions['repository'].now += 901
    assert client.get('/api/config').status_code == 401


def test_absolute_expiry_even_with_continuous_activity(client):
    client.post('/login', json={'password': 'synthetic-password'})
    repo = client.application.extensions['repository']
    for _ in range(5):
        repo.now += 600
        assert client.get('/api/config').status_code == 200
    repo.now += 601
    assert client.get('/api/config').status_code == 401


def test_logout_revokes_copied_cookie(client):
    login = client.post('/login', json={'password': 'synthetic-password'})
    cookie = client.get_cookie('session').value
    assert client.post('/logout', headers={'X-CSRF-Token': login.json['data']['csrf_token']}).status_code == 200
    other = client.application.test_client()
    other.set_cookie('session', cookie)
    assert other.get('/api/config').status_code == 401


def test_database_details_not_returned_or_logged(client, caplog):
    client.post('/login', json={'password': 'synthetic-password'})
    def fail(*args, **kwargs):
        raise RuntimeError('postgresql://admin:' + 'DO_NOT_EXPOSE' + '@private-host/db SELECT secret_column')
    client.application.extensions['repository'].get_setting = fail
    response = client.get('/api/config')
    assert response.status_code == 500 and response.json['error_id']
    assert 'DO_NOT_EXPOSE' not in response.get_data(as_text=True) + caplog.text
    assert 'secret_column' not in response.get_data(as_text=True) + caplog.text
    assert client.application.extensions['repository'].events


def test_no_password_hash_or_session_secret_in_frontend(client):
    client.post('/login', json={'password': 'synthetic-password'})
    for route in ['/', '/api/config', '/static/cloud.js', '/static/login.js']:
        value = client.get(route).get_data(as_text=True)
        assert '$argon2' not in value and 'synthetic-test-session-secret' not in value


def test_production_cookie_and_debug_block(client):
    client.application.config['SESSION_COOKIE_SECURE'] = True
    response = client.post('/login', json={'password': 'synthetic-password'})
    cookie = response.headers['Set-Cookie']
    assert 'Secure' in cookie and 'HttpOnly' in cookie and 'SameSite=Lax' in cookie
    assert client.application.config['SESSION_REFRESH_EACH_REQUEST'] is False
    client.application.debug = True
    assert client.get('/').status_code == 503


def test_non_argon_password_hash_rejected():
    from cloud.security import validate_admin_hash
    with pytest.raises(RuntimeError, match='Argon2id'):
        validate_admin_hash('scrypt:old-hash')


def test_readiness_and_monitoring_requirements(client):
    assert client.get('/health/ready').status_code == 200
    assert client.get('/api/operations').status_code == 401
    client.post('/login', json={'password': 'synthetic-password'})
    assert client.get('/api/operations').status_code == 200
