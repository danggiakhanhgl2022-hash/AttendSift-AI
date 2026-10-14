"""Prevent users mistaking a raw Chatwork dump for the 4-sheet attendance export."""
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]


class RawButtonNesting(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_details = 0
        self.raw_in_advanced = False
        self.labels = []
        self.advanced_closed = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'details':
            self.in_details += 1
        if tag == 'button':
            if attrs.get('id') == 'rawExportButton':
                self.raw_in_advanced = self.in_details > 0
            if attrs.get('id') in {'createButton', 'exportButton'}:
                self.labels.append(attrs.get('id'))

    def handle_endtag(self, tag):
        if tag == 'details':
            self.in_details -= 1


def test_four_sheet_flow_is_primary_and_raw_dump_is_advanced_only():
    html = (ROOT / 'templates/index.html').read_text(encoding='utf-8')
    parser = RawButtonNesting()
    parser.feed(html)
    assert parser.raw_in_advanced
    assert set(parser.labels) == {'createButton', 'exportButton'}
    assert 'Xuất bảng chấm công 4 sheet vào Downloads' in html
    assert 'Tải file tin nhắn THÔ (1 sheet, không tính OT)' in html
    assert 'Cham_cong_MM_YYYY.xlsx' in html


def test_raw_dump_needs_explicit_confirmation_before_download():
    js = (ROOT / 'static/app.js').read_text(encoding='utf-8')
    handler = js.split("$('rawExportButton').onclick=", 1)[1].split("$('importDataForm').onsubmit", 1)[0]
    assert 'confirmAction(' in handler
    assert handler.index('confirmAction(') < handler.index("fetch('/api/export/raw-messages'")
    assert 'không phải bảng chấm công' in handler
    main = js.split('async function exportExcel()', 1)[1].split('async function loadHistory()', 1)[0]
    assert '/export`' in main
    assert 'raw-messages' not in main
