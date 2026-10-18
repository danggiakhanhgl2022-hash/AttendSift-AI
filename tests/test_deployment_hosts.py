"""Deployment URLs work without trusting unrelated tenants or forwarded hosts."""
import pytest
from cloud.hosts import allowed_hosts
from cloud.app import create_app
from cloud.security import PASSWORD_HASHER
from tests.test_cloud_web import MemoryRepository


def test_platform_hosts_still_require_vercel_environment():
    with pytest.raises(RuntimeError):
        allowed_hosts({'VERCEL_URL': 'deployment.vercel.app'})
    assert allowed_hosts({'CHAMCONG_ALLOWED_HOSTS': ' Example.com ,localhost ',
                          'VERCEL_URL': 'ignored.vercel.app'}) == {'example.com', 'localhost'}


@pytest.mark.parametrize('value', ['https://bad.example', '*.vercel.app',
                                  'bad.example/path', 'bad.example:443',
                                  'bad.example,evil.example', '-bad.example', ''])
def test_invalid_platform_metadata_is_ignored(value):
    assert allowed_hosts({'VERCEL': '1', 'VERCEL_URL': value,
                          'CHAMCONG_ALLOWED_HOSTS': 'example.com'}) == {'example.com'}


def test_deployment_host_allows_login_but_keeps_authentication_and_host_checks():
    app = create_app(repository=MemoryRepository(), config={
        'CHAMCONG_SESSION_SECRET': 'synthetic-test-session-secret-1234567890',
        'CHAMCONG_ADMIN_PASSWORD_HASH': PASSWORD_HASHER.hash('synthetic-password'),
        'VERCEL': '1', 'VERCEL_URL': 'project-deployment.vercel.app',
        'VERCEL_BRANCH_URL': 'project-main.vercel.app',
        'VERCEL_PROJECT_PRODUCTION_URL': 'project.vercel.app',
    })
    client = app.test_client()
    for host in ('project-deployment.vercel.app', 'project-main.vercel.app', 'project.vercel.app'):
        assert client.get('/login', base_url='https://' + host).status_code == 200
        assert client.get('/', base_url='https://' + host).status_code == 302
        assert client.get('/api/config', base_url='https://' + host).status_code == 401
    assert client.get('/login', base_url='https://another-project.vercel.app',
                      headers={'X-Forwarded-Host': 'project.vercel.app'}).status_code == 403
