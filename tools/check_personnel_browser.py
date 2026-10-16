"""Optional browser acceptance with installed Edge; synthetic personnel only."""
from pathlib import Path
import json
import sys
import tempfile
import threading
from unittest.mock import patch
from werkzeug.serving import make_server

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def check(app,browser,cloud=False):
    server=make_server('127.0.0.1',0,app,threaded=True)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    context=browser.new_context(viewport={'width':1365,'height':1000})
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('dialog',lambda dialog:dialog.accept())
    try:
        if cloud:
            assert context.request.post(base+'/login',data={'password':'synthetic-password'}).ok
        page.goto(base,wait_until='networkidle')
        assert page.locator('button[data-section="employees"]').count()==1
        page.click('button[data-section="employees"]')
        page.wait_for_function("() => document.querySelector('#employeeCount').textContent.includes('0 nhân viên')")
        page.fill('#employeeName','Lan Demo')
        page.locator('#employeeForm button[type=submit]').click()
        page.wait_for_function("() => document.querySelector('#employeeCount').textContent.includes('1 nhân viên')")
        page.fill('#employeeImportText','Bình Demo')
        page.click('#employeeImport')
        page.wait_for_function("() => document.querySelector('#employeeCount').textContent.includes('2 nhân viên')")
        page.screenshot(path=str(ROOT/'release'/('personnel-cloud.png' if cloud else 'personnel-local.png')))
        params={'month':10,'year':2026,'accept_risk':True}
        result=page.evaluate("""async ({path,data})=>{
            const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content},body:JSON.stringify(data)});
            return {status:response.status,value:await response.json()};
        }""",{'path':'/api/sessions' if cloud else '/api/export/create-session','data':params})
        assert result['status']==200,result
        sid=result['value']['data']['session_id']
        result=page.evaluate("""async path=>{
            const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name="csrf-token"]').content},body:'{}'});
            return {status:response.status,value:await response.json()};
        }""",f'/api/sessions/{sid}/analyze' if cloud else f'/api/export/{sid}/analyze')
        assert result['status']==200,result
        if cloud:
            page.click('button[data-section="export"]')
            page.evaluate("""async id=>{sid=String(id);await loadSession();}""",sid)
            page.select_option('#reviewFilter','all')
            page.locator('#results button').first.click()
        else:
            page.evaluate('async sid=>await openSession(sid)',sid)
            page.select_option('#reviewFilter','all')
            page.locator('#reviewRows button').first.click()
        assert page.locator('#reviewPersonnelGroup').is_visible()
        assert page.locator('#reviewPersonnelEmployee option').count()==3
        assert page.locator('#reviewPersonnelGroup').input_value()=='official'
        assert not errors,errors
        return {'employees_tab':True,'add_and_import':True,'session_analyze':True,
                'review_controls':True,'javascript_errors':errors}
    finally:
        context.close();server.shutdown();thread.join();server.server_close()


def main():
    from playwright.sync_api import sync_playwright
    from src.app.server import create_app
    from tests.test_personnel_cloud_flow import make_app,EmptyAI
    edge=Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
    with tempfile.TemporaryDirectory(prefix='personnel-browser-',dir=ROOT/'release') as temp:
        app=create_app(temp)
        service=app.extensions['services']
        service['config'].set('chatwork_room_id','test-room')
        service['config'].set('ai_api_key','fake-development-key')
        service['export'].sync_service=None
        service['sync'].message_repo if hasattr(service['sync'],'message_repo') else None
        from src.models.database import MessageRepository
        MessageRepository(service['db']).save_messages_batch([dict(
            message_id='demo-1',room_id='test-room',account_id=1,name='Người báo hộ',
            body='Team Demo: ngày 5/10\nLan Demo OT 1h\nAn Demo (CTV) OT 2h',
            send_time='2026-10-05T18:00:00+07:00')])
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(executable_path=str(edge),headless=True)
            try:
                with patch('src.services.export_service.create_ai_adapter',return_value=EmptyAI()):
                    local=check(app,browser)
                cloud=check(make_app(),browser,True)
            finally:browser.close()
    result={'local':local,'cloud':cloud,'real_api_tested':False}
    (ROOT/'release/personnel-browser.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
