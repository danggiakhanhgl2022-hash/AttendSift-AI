"""Verify radial navigation and real-response status handling with mocked API replies."""
from pathlib import Path
import json
import logging
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.app.server import create_app
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright


def main():
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    report={}
    with tempfile.TemporaryDirectory(prefix='attendsift-orb-test-') as temp:
        app=create_app(temp);server=make_server('127.0.0.1',0,app,threaded=True)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(channel='msedge',headless=True,args=['--enable-unsafe-swiftshader'])
                page=browser.new_page(viewport={'width':1600,'height':1000},reduced_motion='reduce')
                errors=[];requests=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('request',lambda req:requests.append((req.method,req.url,req.post_data)))
                page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='networkidle')
                page.locator('.nav [data-section="settings"]').click()
                assert page.locator('#operation-sidebar').is_visible()
                assert page.evaluate('OperationOrb.getState().status')=='idle'
                page.locator('.orbit-center').click()
                assert page.locator('#orb-branches').is_visible()
                rectangles=page.locator('.orbit-center, #orb-branches button').evaluate_all('(nodes)=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}})')
                for i,a in enumerate(rectangles):
                    for b in rectangles[i+1:]:
                        assert not (a['x']<b['right'] and a['right']>b['x'] and a['y']<b['bottom'] and a['bottom']>b['y']), (a,b)
                for key in ['sync','export','history','settings','employees']:
                    page.locator(f'[data-orb-target="{key}"]').click()
                    assert page.locator(f'#{key}-section').is_visible()
                report['radial_branches_open_all_five_original_tabs']=True
                report['branch_boxes_do_not_overlap']=True
                # Reply is mocked here; this test never connects to Chatwork or an AI provider.
                page.route('**/api/config/chatwork/test',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps({'success':True,'data':{'marker':'same-response'}})))
                status=page.evaluate("""() => { window.__orbResult=fetch('/api/config/chatwork/test',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(r=>r.json()); return OperationOrb.getState().status; }""")
                assert status=='busy'
                page.wait_for_function('() => OperationOrb.getState().status === "success"')
                assert page.evaluate('() => window.__orbResult.then(r=>r.data.marker)')=='same-response'
                assert page.locator('#orb-center-state').inner_text()=='Thành công'
                report['busy_then_success_only_after_success_response']=True
                report['original_response_body_preserved']=True
                page.route('**/api/config/ai/test',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps({'success':False,'error':'Mock failure'})))
                page.evaluate("() => { fetch('/api/config/ai/test',{method:'POST',body:'{}'}).catch(()=>{}); }")
                page.wait_for_function('() => OperationOrb.getState().status === "failed"')
                assert page.locator('#orb-center-state').inner_text()!='Thành công'
                report['failed_response_never_shows_success']=True
                page.route('**/api/export/preflight',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps({'success':True,'data':{'can_continue':True,'requires_risk_acceptance':True}})))
                page.evaluate("() => { fetch('/api/export/preflight',{method:'POST',body:'{}'}).catch(()=>{}); }")
                page.wait_for_function('() => OperationOrb.getState().status === "review"')
                assert page.locator('#orb-center-state').inner_text()=='Cần xác nhận'
                report['risk_acceptance_not_automatically_confirmed']=True
                page.route('**/api/sync/run',lambda route:route.abort())
                page.evaluate("() => { fetch('/api/sync/run',{method:'POST',body:'{}'}).catch(()=>{}); }")
                page.wait_for_function('() => OperationOrb.getState().status === "failed"')
                report['network_failure_not_reported_as_success']=True
                page.locator('[data-orb-target="settings"]').click()
                # Show the verified success state in the preview, not a fabricated idle success.
                page.evaluate("() => { fetch('/api/config/chatwork/test',{method:'POST',body:'{}'}).catch(()=>{}); }")
                page.wait_for_function('() => OperationOrb.getState().status === "success"')
                page.screenshot(path=str(ROOT/'ORB_5D_SETTINGS.png'),full_page=True)
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                page.set_viewport_size({'width':390,'height':844})
                page.wait_for_timeout(200)
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                page.screenshot(path=str(ROOT/'ORB_5D_MOBILE.png'),full_page=True)
                page.emulate_media(reduced_motion='reduce')
                assert page.locator('#operation-sidebar').get_attribute('data-motion')=='running'
                report['orb_autoplays_even_when_system_reduces_motion']=True
                page.locator('#dashboard-nav').click()
                page.locator('#dash-motion').select_option('system')
                page.locator('.nav [data-section="settings"]').click()
                page.wait_for_function('() => document.getElementById("operation-sidebar").dataset.motion === "paused"')
                posts=[r for r in requests if r[0]=='POST']
                assert len(posts)==5,posts
                assert all(r[2]=='{}' for r in posts)
                report.update({'request_method_and_body_preserved':True,'intentional_mock_post_count':len(posts),
                    'desktop_mobile_no_overflow':True,'reduced_motion_verified':True,'javascript_errors':errors})
                assert not errors,errors
                browser.close()
        finally:
            server.shutdown();server.server_close()
    (ROOT/'KIEM_TRA_ORB_5D.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
