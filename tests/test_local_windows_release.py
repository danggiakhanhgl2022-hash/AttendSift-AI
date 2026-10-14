"""Static local-portability contract; full launch/build tested on Windows."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_windows_entry_scripts_and_local_no_cloud_database():
    assert (ROOT / 'CAI_DAT_WINDOWS.bat').is_file()
    assert (ROOT / 'CHAY_LOCAL_WINDOWS.bat').is_file()
    assert (ROOT / 'TAO_EXE_WINDOWS.bat').is_file()
    assert (ROOT / 'requirements-local.txt').is_file()
    requirements = [line.split('#', 1)[0].strip().lower() for line in (ROOT / 'requirements-local.txt').read_text(encoding='utf-8').splitlines()]
    assert any(item.startswith('flask==') for item in requirements) and any(item.startswith('openpyxl==') for item in requirements)
    assert not any('psycopg' in item or 'postgres' in item for item in requirements)
    launcher = (ROOT / 'tools/run_local.py').read_text(encoding='utf-8')
    assert "'--headless'" in launcher and "'8766'" in launcher


def test_local_uses_sqlite_loopback_and_four_sheet_template():
    server = (ROOT / 'src/app/server.py').read_text(encoding='utf-8')
    paths = (ROOT / 'src/app/paths.py').read_text(encoding='utf-8')
    launcher = (ROOT / 'src/app/launcher.py').read_text(encoding='utf-8')
    assert "'chamcong.db'" in server
    assert "'127.0.0.1'" in launcher
    assert "'data','outputs','backups','logs','config'" in launcher
    assert "'Downloads'" in paths
    assert (ROOT / 'templates/template.xlsx').is_file()
