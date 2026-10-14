"""API regressions with isolated data and no external services."""
import io
from pathlib import Path
import re
from unittest.mock import patch

import pytest

from src.app.server import create_app
from src.models.database import MessageRepository
from src.adapters.ai_adapters import AIAdapterError


@pytest.fixture
def api(tmp_path):
    app = create_app(str(tmp_path))
    client = app.test_client()
    html = client.get('/').get_data(as_text=True)
    token = re.search(r'name="csrf-token" content="([^"]+)"', html)[1]
    return app, client, {'X-CSRF-Token': token}, tmp_path


@pytest.mark.parametrize('route', ['/api/history', '/api/sync/messages', '/api/export/sessions'])
@pytest.mark.parametrize('limit', ['-1', '0', '5001', 'garbage', '1.5', ''])
def test_invalid_limit_is_rejected(api, route, limit):
    _, client, _, _ = api
    response = client.get(route, query_string={'limit': limit})
    assert response.status_code == 400
    assert response.json['success'] is False


def test_message_limit_selects_latest_records(api):
    app, client, _, _ = api
    app.extensions['services']['config'].set('chatwork_room_id', 'r')
    repo = MessageRepository(app.extensions['services']['db'])
    repo.save_messages_batch([
        {'message_id': str(i), 'room_id': 'r', 'body': f'Message {i}',
         'send_time': f'2026-09-01T10:0{i}:00+07:00'} for i in range(3)
    ])
    response = client.get('/api/sync/messages?limit=2')
    assert response.status_code == 200
    assert [item['message_id'] for item in response.json['data']] == ['2', '1']


def test_dashboard_counts_all_events_not_only_first_hundred(api):
    app, client, _, _ = api
    actions = app.extensions['services']['actions']
    for i in range(125):
        actions.log_event(f'test-{i}', 'sync', 'test', 'success')
    actions.log_event('failed', 'export', 'test', 'failed')
    db = app.extensions['services']['db']
    with db._get_connection() as conn:
        conn.execute("INSERT INTO action_events(operation_id,action_type,source,status,action_time,created_at) VALUES('old','sync','test','success','2000-01-01T00:00:00+07:00','2000-01-01T00:00:00+07:00')")
    response = client.get('/api/history/dashboard')
    assert response.status_code == 200
    data = response.json['data']
    assert data['sync_count'] == data['success_count'] == 125
    assert data['failed_count'] == data['export_count'] == 1
    assert len(data['recent_events']) == 20


@pytest.mark.parametrize('provider', [None, 17, [], {}, '', 'unknown'])
@pytest.mark.parametrize('route', ['/api/config/ai', '/api/config/ai/test'])
def test_invalid_provider_is_client_error(api, provider, route):
    _, client, headers, _ = api
    response = client.post(route, json={'provider': provider, 'api_key': 'fake'}, headers=headers)
    assert response.status_code == 400
    assert response.json['success'] is False


def test_ai_transport_error_is_redacted(api):
    _, client, headers, _ = api
    with patch('src.services.config_service.create_ai_adapter', side_effect=AIAdapterError('SECRET-TRANSPORT-KEY')):
        response = client.post('/api/config/ai/test', json={'provider': 'openai', 'api_key': 'fake'}, headers=headers)
    assert response.status_code == 400
    assert 'SECRET-TRANSPORT-KEY' not in response.get_data(as_text=True)


def test_invalid_room_keeps_previous_chatwork_settings(api):
    app, client, headers, _ = api
    config = app.extensions['services']['config']
    config.set('chatwork_api_key', 'old-fake-key')
    config.set('chatwork_room_id', 'old-room')
    with patch('src.services.config_service.ChatworkAdapter') as adapter:
        adapter.return_value.test_connection.return_value = {'name': 'test'}
        adapter.return_value.get_rooms.return_value = [{'room_id': 'available', 'name': 'Allowed'}]
        response = client.post('/api/config/chatwork', headers=headers,
                               json={'api_key': 'new-fake-key', 'room_id': 'forbidden'})
    assert response.status_code == 400
    assert config.get('chatwork_api_key') == 'old-fake-key'
    assert config.get('chatwork_room_id') == 'old-room'


def test_session_list_is_bounded_and_does_not_expose_snapshot(api):
    app, client, _, _ = api
    sessions = app.extensions['services']['sessions']
    for i in range(3):
        sessions.create_session(f's{i}', 9, 2026)
    with app.extensions['services']['db']._get_connection() as conn:
        for i in range(3):
            conn.execute('UPDATE export_sessions SET created_at=?,snapshot=? WHERE session_id=?',
                         (f'2026-09-01T10:0{i}:00+07:00', '["private message"]', f's{i}'))
    response = client.get('/api/export/sessions?limit=2')
    assert response.status_code == 200
    assert [item['session_id'] for item in response.json['data']] == ['s2', 's1']
    assert 'private message' not in response.get_data(as_text=True)


def test_separate_app_data_directories_do_not_share_config(api, tmp_path):
    app, _, _, _ = api
    other = create_app(str(tmp_path / 'other'))
    app.extensions['services']['config'].set('isolation_marker', 'first')
    assert other.extensions['services']['config'].get('isolation_marker') is None
    assert app.extensions['services']['db'].db_path != other.extensions['services']['db'].db_path


def test_settings_do_not_require_or_offer_an_excel_template(api):
    app, client, headers, _ = api
    app.extensions['services']['config'].set('excel_template', 'missing-old-template.xlsx')
    response = client.get('/api/config')
    assert 'template' not in response.json['data']
    html = client.get('/').get_data(as_text=True)
    assert 'id="templateForm"' not in html
    assert 'id="templateFile"' not in html
    assert client.post('/api/config/template', json={'path': 'anything'}, headers=headers).status_code == 404
    assert client.post('/api/config/template/upload', data={}, headers=headers).status_code == 404


def test_raw_export_reads_database_without_ai_or_sync(api):
    from openpyxl import load_workbook
    app, client, headers, _ = api
    services = app.extensions['services']
    services['config'].set('chatwork_room_id', 'r')
    repo = MessageRepository(services['db'])
    body = 'Tester\nTesterB PRODUCTIONS COMPANY LIMITED\nOT 2 hours\nroger\n1'
    repo.save_messages_batch([
        {'message_id':mid, 'room_id':room, 'name':'Tester', 'body':body, 'send_time':date}
        for mid,room,date in [
            ('before','r','2026-08-16T23:59:59+07:00'),
            ('start','r','2026-08-17T00:00:00+07:00'),
            ('end','r','2026-09-30T23:59:59.999999+07:00'),
            ('after','r','2026-10-01T00:00:00+07:00'),
            ('other','other','2026-09-01T00:00:00+07:00')]])
    with patch.object(services['sync'],'catch_up',side_effect=AssertionError('Network forbidden')), patch.object(services['export'],'analyze',side_effect=AssertionError('AI forbidden')):
        response=client.post('/api/export/raw-messages',json={'month':9,'year':2026},headers=headers)
    assert response.status_code==200
    assert response.headers['X-Message-Count']=='2'
    workbook=load_workbook(io.BytesIO(response.data))
    rows=list(workbook.active.values)
    assert [r[0] for r in rows[1:]]==['start','end']
    assert rows[1][4]=='Tester\nOT 2 hours'
    assert len(rows[0]) == 5
    assert rows[0][4] == 'Nội dung tin nhắn'
    assert repo.get_by_id('start')['body']==body


def test_raw_export_empty_and_invalid_month(api):
    app,client,headers,_=api
    app.extensions['services']['config'].set('chatwork_room_id','r')
    for payload in [{'month':9,'year':2026},{'month':13,'year':2026}]:
        response=client.post('/api/export/raw-messages',json=payload,headers=headers)
        assert response.status_code==400
        assert response.json['success'] is False


def test_raw_export_interface_preserves_vietnamese(api):
    _, client, _, _ = api
    html = client.get('/').get_data(as_text=True)
    assert 'rawExportAdvanced' in html
    assert 'Tải file tin nhắn THÔ' in html
    assert 'Xu?t tin nh?n' not in html
    javascript = client.get('/static/app.js').get_data(as_text=True)
    assert 'Khoảng xuất:' in javascript
    assert 'Kho?ng xu?t:' not in javascript
    assert 'periodStatus' in javascript
