"""Cloud Neural Terminal reads durable data and preserves authentication and CSRF."""
import hashlib
import pytest
from cloud.app import create_app
from cloud.security import PASSWORD_HASHER
from tests.test_cloud_web import MemoryRepository
from tests.test_workbook_view import workbook_bytes
from tools.sync_cloud_ui import ROOT, ASSETS


class DashboardRepository(MemoryRepository):
    def __init__(self):
        super().__init__()
        self.content = workbook_bytes()
        self.digest = hashlib.sha256(self.content).hexdigest()

    def dashboard_messages(self, room):
        assert room == 'synthetic-room'
        return 7, [{'message_id': 'demo', 'send_time': '2026-10-18T08:00:00+07:00'}]

    def dashboard_history(self):
        return dict(success_count=3, failed_count=0, sync_count=1, recent_events=[])

    def get_setting(self, key, default=None):
        if key == 'room':
            return {'room_id': 'synthetic-room', 'room_name': 'Nhóm Demo'}
        return default

    def sessions(self):
        return [dict(session_id='demo', month=10, year=2026, status='exported')]

    def session(self, sid):
        if sid != 'demo':
            return None
        return dict(session_id=sid, month=10, year=2026, status='exported', snapshot=[],
                    results=[], completed=0, ai_settings={})

    def file(self, sid):
        return dict(filename='demo.xlsx', content=self.content, sha256=self.digest)

    def messages(self, room, start, end):
        return []

    def history(self):
        return []


def dashboard_app():
    repo = DashboardRepository()
    app = create_app(repository=repo, config={
        'CHAMCONG_SESSION_SECRET': 'synthetic-dashboard-session-secret-123456789',
        'CHAMCONG_ADMIN_PASSWORD_HASH': PASSWORD_HASHER.hash('synthetic-password'),
        'CHAMCONG_ALLOWED_HOSTS': 'localhost,127.0.0.1', 'CHAMCONG_INSECURE_LOCAL': '1',
    })
    return app, repo


def test_dashboard_auth_data_and_workbook_integrity():
    app, repo = dashboard_app()
    client = app.test_client()
    for path in ('/api/dashboard/state', '/api/sessions/demo/workbook-summary'):
        assert client.get(path).status_code == 401
    login = client.post('/login', json={'password': 'synthetic-password'})
    csrf = login.json['data']['csrf_token']
    value = client.get('/api/dashboard/state').json['data']
    assert value['sync']['message_count'] == 7
    assert value['sync']['room_name'] == 'Nhóm Demo'
    assert value['history']['success_count'] == 3
    assert client.get('/api/sessions/missing/workbook-summary').status_code != 200
    assert client.get('/api/sessions/demo/workbook-summary').json['data']['people'][0]['ot'] == 120
    repo.digest = 'tampered'
    assert client.get('/api/sessions/demo/workbook-summary').status_code != 200
    assert client.post('/api/dashboard/workbook-summary').status_code == 403
    from io import BytesIO
    upload = client.post('/api/dashboard/workbook-summary',
        headers={'X-CSRF-Token': csrf}, data={'file': (BytesIO(repo.content), 'demo.xlsx')})
    assert upload.status_code == 200
    assert upload.json['data']['people'][0]['ot'] == 120
    assert client.post('/api/dashboard/workbook-summary', headers={'X-CSRF-Token': csrf},
        data={'file': (BytesIO(b'invalid workbook'), 'demo.xlsx')}).status_code != 200


def test_session_validation_explains_acceptance_and_missing_messages():
    app, repo = dashboard_app()
    client = app.test_client()
    login = client.post('/login', json={'password': 'synthetic-password'})
    headers = {'X-CSRF-Token': login.json['data']['csrf_token']}
    data = {'month': 10, 'year': 2026}
    response = client.post('/api/sessions', json=data, headers=headers)
    assert response.status_code == 400
    assert 'Tôi đồng ý tạo bản tạm' in response.json['error']
    response = client.post('/api/sessions', json={**data, 'accept_risk': True}, headers=headers)
    assert response.status_code == 400
    assert 'Đồng bộ' in response.json['error']
    # Arbitrary ValueErrors from dependencies still must not disclose private details.
    def fail(*args):
        raise ValueError('synthetic-private-database-detail')
    repo.messages = fail
    response = client.post('/api/sessions', json={**data, 'accept_risk': True}, headers=headers)
    assert 'synthetic-private-database-detail' not in response.get_data(as_text=True)


@pytest.mark.parametrize('name', ASSETS)
def test_shared_assets_match_both_cloud_delivery_paths(name):
    if name.endswith('.png'):
        assert (ROOT / 'static' / name).read_bytes() == (ROOT / 'cloud/static' / name).read_bytes()
        assert (ROOT / 'static' / name).read_bytes() == (ROOT / 'public/static' / name).read_bytes()
    else:
        # Existing upstream text blobs mix LF/CRLF; compare decoded content across OSes.
        assert (ROOT / 'static' / name).read_text(encoding='utf-8') == (ROOT / 'cloud/static' / name).read_text(encoding='utf-8')
        assert (ROOT / 'static' / name).read_text(encoding='utf-8') == (ROOT / 'public/static' / name).read_text(encoding='utf-8')
