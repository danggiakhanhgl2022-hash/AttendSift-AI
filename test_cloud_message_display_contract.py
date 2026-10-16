"""Static deployment contract, alongside the executable Node UI test.

These checks work without Flask/PostgreSQL/Chatwork credentials.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_both_cloud_asset_paths_are_kept_in_sync():
    assert (ROOT / 'cloud/static/cloud.js').read_bytes() == (ROOT / 'public/static/cloud.js').read_bytes()


def test_cloud_template_displays_correct_date_order_and_feedback():
    html = (ROOT / 'cloud/templates/index.html').read_text(encoding='utf-8')
    assert html.index('Từ ngày<input id="messageStart"') < html.index('Đến ngày<input id="messageEnd"')
    assert 'id="messageViewSummary"' in html
    assert '/static/cloud.js?v=20261016-exportlater' in html


def test_sync_refresh_and_filter_validation_are_present():
    js = (ROOT / 'cloud/static/cloud.js').read_text(encoding='utf-8')
    assert 'const loaded=await loadMessages()' in js
    assert "if(start&&end&&start>end)" in js
    assert "$('sourceMonth').addEventListener('change'" in js
    assert "messageDataLoaded=true;" in js
    assert "timeZone:'Asia/Ho_Chi_Minh'" in js
