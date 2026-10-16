"""Exercise real Cloud HTTP/session/export paths with synthetic storage and AI."""
import copy
from contextlib import contextmanager
from io import BytesIO
import openpyxl
from cloud.app import create_app
from cloud.security import PASSWORD_HASHER
from tests.test_cloud_connections import SettingsRepository


class FakeRepo(SettingsRepository):
    def __init__(self):
        super().__init__()
        self.records = {}
        self.files = {}
        self.source = [dict(message_id='demo-1', room_id='123', account_id=1,
                            name='Người báo hộ', body='Team Demo: ngày 5/10\nLan Demo OT 1h\nAn Demo (CTV) OT 2h',
                            send_time='2026-10-05T18:00:00+07:00')]

    @contextmanager
    def lease(self,*args,**kwargs):
        yield 'synthetic-owner'

    def messages(self,*args):
        return copy.deepcopy(self.source)

    def create_session(self, value):
        existing=next((v for v in self.records.values() if v['fingerprint']==value['fingerprint']),None)
        if existing:return copy.deepcopy(existing)
        value={**copy.deepcopy(value), 'status':'prepared','results':[],'raw_events':[],'completed':[]}
        self.records[value['session_id']]=value
        return copy.deepcopy(value)

    def session(self,sid):
        return copy.deepcopy(self.records.get(sid))

    def sessions(self):
        return []

    def save_analysis(self,sid,owner,**values):
        self.records[sid].update(copy.deepcopy(values))

    def save_file(self,sid,owner,filename,data):
        import hashlib
        self.files[sid]={'filename':filename,'content':data,'sha256':hashlib.sha256(data).hexdigest()}
        self.records[sid]['status']='exported'

    def file(self,sid):
        return self.files.get(sid)


class EmptyAI:
    def __init__(self,**kwargs):pass
    def analyze_attendance(self,*args):return []


def make_app(repo=None):
    return create_app(repository=repo or FakeRepo(),ai_factory=EmptyAI,config={
        'CHAMCONG_SESSION_SECRET':'synthetic-flow-session-secret-1234567890',
        'CHAMCONG_ADMIN_PASSWORD_HASH':PASSWORD_HASHER.hash('synthetic-password'),
        'CHAMCONG_ALLOWED_HOSTS':'localhost,127.0.0.1',
        'CHAMCONG_INSECURE_LOCAL':'1','CHATWORK_ROOM_ID':'123',
        'GEMINI_API_KEY':'synthetic-ai-key','CHATWORK_API_KEY':'synthetic-chatwork-key'})


def login(client):
    result=client.post('/login',json={'password':'synthetic-password'})
    assert result.status_code==200
    return {'X-CSRF-Token':result.json['data']['csrf_token']}


def test_cloud_session_freezes_roster_and_exports_five_sheets():
    repo=FakeRepo();client=make_app(repo).test_client();headers=login(client)
    assert client.post('/api/employees/import',json={'employees':['Lan Demo','Bình Demo']},headers=headers).status_code==200
    employees=client.get('/api/employees').json['data']['employees']
    created=client.post('/api/sessions',json={'month':10,'year':2026,'accept_risk':True},headers=headers)
    assert created.status_code==200
    sid=created.json['data']['session_id']
    client.post('/api/employees/'+employees[0]['id'],json={'active':False},headers=headers)
    analyzed=client.post('/api/sessions/'+sid+'/analyze',json={},headers=headers)
    assert analyzed.status_code==200,analyzed.json
    results=repo.records[sid]['results']
    assert {e['classification'] for e in results if not e.get('is_excluded')}=={'official','contractor'}
    exported=client.post('/api/sessions/'+sid+'/export',json={},headers=headers)
    assert exported.status_code==200,exported.json
    data=client.get(exported.json['data']['download_url'])
    workbook=openpyxl.load_workbook(BytesIO(data.data),data_only=True)
    try:
        assert workbook.sheetnames[-1]=='5_CTV'
        assert workbook['3_TONG_KET']['I5'].value==60
        assert workbook['5_CTV']['E5'].value==120
    finally:workbook.close()


def test_cloud_empty_roster_is_explicit_and_registry_change_creates_new_session():
    repo=FakeRepo();client=make_app(repo).test_client();headers=login(client)
    body={'month':10,'year':2026,'accept_risk':True}
    assert client.post('/api/sessions',json=body,headers=headers).status_code==400
    first=client.post('/api/sessions',json={**body,'confirm_empty_roster':True},headers=headers).json['data']
    client.post('/api/employees',json={'full_name':'Lan Demo'},headers=headers)
    second=client.post('/api/sessions',json=body,headers=headers).json['data']
    assert first['session_id']!=second['session_id']


def test_cloud_reviewer_can_reclassify_with_snapshot_and_keeps_audit():
    repo=FakeRepo();client=make_app(repo).test_client();headers=login(client)
    client.post('/api/employees/import',json={'employees':['Lan Demo','Bình Demo']},headers=headers)
    people=client.get('/api/employees').json['data']['employees']
    sid=client.post('/api/sessions',json={'month':10,'year':2026,'accept_risk':True},headers=headers).json['data']['session_id']
    client.post('/api/sessions/'+sid+'/analyze',json={},headers=headers)
    contractor=next(e for e in repo.records[sid]['results'] if e.get('classification')=='contractor')
    result=client.post('/api/sessions/'+sid+'/review',json={
        'event_id':contractor['event_id'],'changes':{'classification':'official','employee_id':people[1]['id']}},headers=headers)
    assert result.status_code==200,result.json
    revised=next(e for e in repo.records[sid]['results'] if e['event_id']==contractor['event_id'])
    assert revised['employee_name']=='Bình Demo'
    assert revised['classification_confirmed']
    assert any(args[0]=='review' for args,kwargs in repo.events)
