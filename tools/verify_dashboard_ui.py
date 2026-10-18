"""Exercise live/read-only dashboard, demo isolation, motion and original forms."""
from pathlib import Path
import json
import logging
import sys
import tempfile
import threading
import io
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.app.server import create_app
from src.models.database import MessageRepository
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright


def main():
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    report = {}
    with tempfile.TemporaryDirectory(prefix='attendsift-dashboard-test-') as temp:
        app = create_app(temp)
        services = app.extensions['services']
        services['config'].set('chatwork_room_id', '123')
        services['config'].set('chatwork_room_name', 'Phòng kiểm thử giả lập')
        services['employees'].import_entries([{'full_name': 'Nguyễn Minh Quân', 'employee_code': 'DEMO01'}])
        messages = MessageRepository(services['db'])
        def message(index):
            return dict(message_id='DEMO-' + str(index), room_id='123', account_id='101',
                        name='Người kiểm thử', body='Nội dung giả lập', send_time='2026-10-16T16:30:00+07:00')
        messages.save_messages_batch([message(i) for i in range(8)])
        server = make_server('127.0.0.1', 0, app, threaded=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        requests = []
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel='msedge', headless=True, args=['--enable-unsafe-swiftshader'])
                page = browser.new_page(viewport={'width':1600, 'height':1100},reduced_motion='reduce')
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda req: requests.append((req.method, req.url)))
                page.goto(f'http://127.0.0.1:{server.server_port}', wait_until='networkidle')
                page.wait_for_function('() => window.Dashboard5D?.getState().hasData')
                page.locator('#dash-brain-slot').scroll_into_view_if_needed()
                page.wait_for_function('() => CinematicScene.getState().frames > 2')
                assert not page.evaluate('CinematicScene.getState().paused')
                assert page.evaluate('Dashboard5D.getState().level')>0
                report['autoplays_on_start_even_when_system_reduces_motion']=True
                assert page.locator('[data-metric="messages"]').get_attribute('data-value') == '8'
                assert page.locator('[data-metric="employees"]').get_attribute('data-value') == '1'
                assert page.locator('[data-metric="events"]').inner_text() == '—'
                assert page.locator('#dash-message-scope').inner_text().startswith('8 ')
                page.locator('#dash-refresh').click()
                page.wait_for_function('() => !Dashboard5D.getState().loading')
                assert page.locator('[data-metric="messages"]').get_attribute('data-value') == '8'
                messages.save_messages_batch([message(8)])
                page.locator('#dash-refresh').click()
                page.wait_for_function('() => Dashboard5D.getState().messages === 9')
                page.wait_for_timeout(900)
                assert page.locator('[data-metric="messages"]').inner_text() == '9'
                report['live_counts_match_database'] = True
                report['unchanged_data_does_not_drift'] = True
                report['new_message_updates_counter'] = True
                # Verify real rendered pixels move in EACH signature, not just CSS names.
                page.locator('.dash-metrics').scroll_into_view_if_needed()
                first=[Image.open(io.BytesIO(page.locator('.panel-signature').nth(i).screenshot())).convert('RGB') for i in range(4)]
                page.wait_for_timeout(380)
                second=[Image.open(io.BytesIO(page.locator('.panel-signature').nth(i).screenshot())).convert('RGB') for i in range(4)]
                assert all(ImageChops.difference(a,b).getbbox() for a,b in zip(first,second))
                report['all_four_signatures_have_visible_pixel_motion']=True
                # Identical GET refreshes must preserve the existing chart animation instance.
                marker=page.locator('#dash-message-chart svg')
                marker.evaluate('n=>n.dataset.testIdentity="preserved"')
                orbit=page.locator('.panel-signature .fx-orbit')
                before=orbit.evaluate('n=>n.getAnimations()[0].currentTime')
                page.locator('#dash-refresh').click()
                page.wait_for_function('() => !Dashboard5D.getState().loading')
                assert marker.get_attribute('data-test-identity')=='preserved'
                assert orbit.evaluate('n=>n.getAnimations()[0].currentTime')>before
                report['unchanged_poll_preserves_animation_clock']=True
                frames=[]
                for _ in range(12):
                    frames.append(Image.open(io.BytesIO(page.locator('.dash-metrics').screenshot())).convert('RGB'))
                    page.wait_for_timeout(140)
                preview=ROOT/'docs/images/dashboard-motion-preview.gif';preview.parent.mkdir(parents=True,exist_ok=True)
                frames[0].save(preview,save_all=True,append_images=frames[1:],duration=200,loop=0)
                # A session contributes non-excluded rows only; ambiguous rows remain review items.
                sessions = services['sessions']
                sessions.create_session('DEMO-SESSION', 10, 2026)
                fixture_rows = [dict(event_id='EVT-'+str(i),source_id='DEMO-0',employee_name='Demo',
                    event_date='2026-10-16',event_type='Tăng ca',is_excluded=i==3,needs_review=i==1)
                    for i in range(4)]
                sessions.save_results('DEMO-SESSION',fixture_rows)
                with services['db']._get_connection() as conn:
                    for i, classification in enumerate(['official','unresolved','contractor','unresolved']):
                        conn.execute('UPDATE ai_results SET payload=?,review_state=? WHERE event_id=?',
                            (json.dumps({'classification':classification,'ot_minutes':120 if i==0 else 0}), 'pending' if i in [1,3] else 'confirmed','EVT-'+str(i)))
                    conn.execute('UPDATE export_sessions SET snapshot=? WHERE session_id=?',
                        (json.dumps([{'message_id':'DEMO-0','name':'Nguồn kiểm thử','send_time':'2026-10-17T08:00:00+07:00','body':'Báo cáo gốc: Demo OT 2h ngày 16/10. <script>BAD()</script>'}]),'DEMO-SESSION'))
                    conn.commit()
                sessions.update_session('DEMO-SESSION',status='analyzing')
                page.locator('#dash-refresh').click()
                page.wait_for_function('() => Dashboard5D.getState().processStatus === "analyzing"')
                assert page.locator('#process-state').inner_text() == 'AI đang phân tích'
                assert 'Báo cáo gốc' in page.locator('#process-source').inner_text()
                assert 'Chưa có kết quả hoàn tất' in page.locator('#process-result').inner_text()
                assert page.locator('#process-source script').count() == 0
                assert page.evaluate('Dashboard5D.getState().rows') is None
                report['analyzing_stream_uses_snapshot_without_premature_results'] = True
                sessions.update_session('DEMO-SESSION',status='review')
                page.locator('#dash-refresh').click()
                page.wait_for_function('() => Dashboard5D.getState().rows === 3')
                assert 'cần kiểm tra' in page.locator('#process-state').inner_text()
                assert 'Demo' in page.locator('#process-result').inner_text()
                report['completed_stream_uses_saved_results_and_preserves_review'] = True
                assert page.locator('[data-metric="pending"]').get_attribute('data-value') == '1'
                report['session_excludes_removed_rows_and_counts_pending'] = True
                page.locator('#dash-explain-row').select_option('0')
                evidence=page.locator('#dash-explanation-steps').inner_text()
                assert 'Báo cáo gốc: Demo OT 2h ngày 16/10.' in evidence
                assert '120 phút' in evidence and '2026-10-16' in evidence
                assert page.locator('#dash-explanation-steps script').count()==0
                page.locator('#dash-explain-row').select_option('1')
                assert 'Cần kiểm tra' in page.locator('#dash-explanation-steps').inner_text()
                report['explanation_uses_session_snapshot_not_other_room_messages'] = True
                report['explanation_escapes_source_html_and_keeps_pending'] = True
                animation_before=page.evaluate('Dashboard5D.getState().animationTime')
                page.mouse.move(10,10);page.wait_for_timeout(200)
                assert page.evaluate('Dashboard5D.getState().animationTime')>animation_before
                assert page.locator('[data-metric="messages"]').get_attribute('data-value')=='9'
                report['motion_continues_without_changing_real_counts'] = True
                for key in ['sync','export','history','settings','employees']:
                    page.locator(f'.nav [data-section="{key}"]').click()
                    assert page.locator(f'#{key}-section').is_visible()
                    assert page.locator('#control-dashboard').is_hidden()
                page.locator('#dashboard-nav').click()
                assert page.locator('#control-dashboard').is_visible()
                report['original_five_tabs_accessible'] = True
                page.locator('.nav [data-section="settings"]').click()
                assert page.locator('#settings-section .card').first.evaluate("n=>getComputedStyle(n,'::before').animationName")=='workspace-aura'
                report['working_forms_have_independent_ambient_effects'] = True
                page.locator('#dashboard-nav').click()
                page.locator('#dash-source').select_option('demo')
                page.wait_for_function('() => Dashboard5D.getState().mode === "demo" && Dashboard5D.getState().messages > 100')
                assert 'GIẢ LẬP' in page.locator('#dash-source-badge').inner_text()
                for level in ['light','strong','off']:
                    page.locator('#dash-motion').select_option(level)
                    state = page.evaluate('Dashboard5D.getState()')
                    assert (state['level'] == 0) if level == 'off' else (state['level'] > 0)
                page.locator('#dash-motion').select_option('strong')
                page.locator('#dash-follow').check()
                page.wait_for_function('() => document.querySelectorAll(".chart-tracer").length > 0')
                assert page.locator('.chart-tracer').first.evaluate('n=>getComputedStyle(n).animationName')=='chart-trace'
                assert page.locator('.class-donut').evaluate("n=>getComputedStyle(n,'::after').animationName")=='classification-orbit'
                assert page.locator('#dash-log li').first.evaluate("n=>getComputedStyle(n,'::before').animationName")=='log-highlight'
                tracer=page.locator('.chart-tracer').first.element_handle()
                before_animation=tracer.evaluate('n=>n.getAnimations()[0].currentTime')
                page.wait_for_timeout(200)
                # A demo tick may replace its fake chart with new data during the sample.
                assert tracer.evaluate('(n,before)=>!n.isConnected || n.getAnimations()[0].currentTime>before',before_animation)
                report['distinct_panel_animations_running_continuously'] = True
                page.wait_for_function('() => CinematicScene.getState().frames > 2')
                page.locator('.cinematic-toggle').click()
                assert page.evaluate('Dashboard5D.getState().level') == 0
                assert page.locator('.chart-tracer').first.evaluate('n=>getComputedStyle(n).animationPlayState')=='paused'
                before = page.evaluate('CinematicScene.getState().frames')
                page.wait_for_timeout(200)
                assert page.evaluate('CinematicScene.getState().frames') == before
                page.locator('.cinematic-toggle').click()
                page.emulate_media(reduced_motion='reduce')
                assert page.evaluate('Dashboard5D.getState().level')>0
                page.locator('#dash-motion').select_option('system')
                assert page.evaluate('Dashboard5D.getState().level') == 0
                page.wait_for_function('() => CinematicScene.getState().paused')
                page.emulate_media(reduced_motion='no-preference')
                page.locator('#dash-motion').select_option('strong')
                page.wait_for_timeout(1000)
                page.screenshot(path=str(ROOT/'DASHBOARD_5D_DESKTOP.png'), full_page=True)
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                page.set_viewport_size({'width':390,'height':844})
                page.wait_for_timeout(250)
                page.screenshot(path=str(ROOT/'DASHBOARD_5D_MOBILE.png'), full_page=True)
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
                # Returning from demo must display the real data again, never write the demo.
                page.locator('#dash-source').select_option('live')
                page.wait_for_function('() => Dashboard5D.getState().messages === 9')
                assert len(messages.get_by_room('123')) == 9
                report['demo_isolated_and_labeled'] = True
                # A failed refresh must preserve previous counters and mark them as stale.
                page.route('**/api/history/dashboard', lambda route: route.fulfill(status=503, body='offline'))
                page.locator('#dash-refresh').click()
                page.wait_for_function('() => Dashboard5D.getState().error')
                assert page.locator('[data-metric="messages"]').get_attribute('data-value') == '9'
                assert 'cũ' in page.locator('#dash-connection').inner_text()
                report.update({'error_keeps_data_and_marks_stale':True, 'motion_levels_verified':True,
                    'pause_verified':True, 'reduced_motion_verified':True, 'desktop_mobile_no_overflow':True,
                    'javascript_errors':errors, 'api_mutation_requests':[r for r in requests if r[0] != 'GET']})
                assert not errors, errors
                assert not report['api_mutation_requests'], report['api_mutation_requests']
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
    (ROOT/'KIEM_TRA_DASHBOARD_5D.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
