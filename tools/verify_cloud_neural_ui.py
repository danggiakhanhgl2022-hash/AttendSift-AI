"""Browser acceptance of the Cloud UI with synthetic data and no external API calls."""
from pathlib import Path
import json
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
from tests.test_cloud_dashboard import dashboard_app


def main():
    app, repo = dashboard_app()
    server = make_server('127.0.0.1', 0, app, threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    output = ROOT / 'artifacts/cloud-neural'
    output.mkdir(parents=True, exist_ok=True)
    errors, failed, writes = [], [], []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='msedge', headless=True,
                                         args=['--enable-unsafe-swiftshader'])
            page = browser.new_page(viewport={'width': 1600, 'height': 1100})
            base = f'http://127.0.0.1:{server.server_port}'
            page.goto(base + '/login')
            login = page.request.post(base + '/login', data={'password': 'synthetic-password'})
            assert login.ok, login.text()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
            page.on('response', lambda response: failed.append([response.status, response.url]) if response.status >= 400 else None)
            page.on('request', lambda request: writes.append(request.url) if request.method == 'POST' else None)
            page.goto(base, wait_until='networkidle')
            page.wait_for_function("() => document.querySelector('#people-ot')?.textContent === '120'")
            page.locator('.nav [data-section="export"]').click()
            page.locator('#analyzeButton').click()
            assert 'Tôi đồng ý tạo bản tạm' in page.locator('#notice').inner_text()
            assert page.locator('#notice').get_attribute('data-kind') == 'error'
            assert not writes, writes
            page.locator('#dashboard-nav').click()
            assert page.locator('#control-dashboard.reference-console').is_visible()
            assert page.locator('[data-metric="messages"]').inner_text() == '7'
            page.wait_for_function('() => CinematicScene.getState().frames > 3')
            page.screenshot(path=str(output / 'desktop.png'), full_page=True)
            page.locator('#dash-source').select_option('demo')
            page.wait_for_function("() => Dashboard5D.getState().mode === 'demo' && document.querySelector('#control-dashboard').dataset.error === 'false'")
            page.wait_for_function("() => document.querySelector('.class-donut') !== null")
            page.locator('#dash-source').select_option('live')
            page.wait_for_function("() => document.querySelector('#people-ot')?.textContent === '120'")
            for section in ('sync', 'export', 'history', 'settings', 'employees'):
                page.locator(f'.nav [data-section="{section}"]').click()
                assert page.locator('#' + section).is_visible()
                assert not page.locator('#control-dashboard').is_visible()
            page.locator('#dashboard-nav').click()
            page.locator('#dash-open-evidence').click()
            assert page.locator('#export').is_visible()
            page.locator('#dashboard-nav').click()
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(300)
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
            page.screenshot(path=str(output / 'mobile.png'), full_page=True)
            repo.sessions = lambda: []
            page.reload(wait_until='networkidle')
            page.wait_for_function("() => document.querySelector('#control-dashboard')?.dataset.error === 'false'")
            assert page.locator('#people-count').inner_text() == '—'
            assert not errors, errors
            assert not failed, failed
            assert not writes, writes
            browser.close()
        report = dict(desktop=True, mobile=True, cloud_excel=True, original_tabs=True,
                      neural_animation=True, javascript_errors=errors, failed_requests=failed,
                      unintended_posts=writes)
        (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
