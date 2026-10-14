"""Read-only local prerequisites and Excel template check, no key disclosure."""
import importlib
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    checks = {}
    checks['Python 3.11-3.13 x64'] = ((3,11) <= sys.version_info[:2] <= (3,13)
                                     and sys.maxsize > 2**32)
    checks['Windows OS'] = os.name == 'nt'
    for name in ['flask','werkzeug','requests','openpyxl','pytz']:
        try: importlib.import_module(name); checks['Library '+name] = True
        except ImportError: checks['Library '+name] = False
    try:
        from src.utils.excel_export import builtin_workbook_path, verify_workbook
        verify_workbook(builtin_workbook_path())
        checks['Four-sheet template'] = True
    except Exception:
        checks['Four-sheet template'] = False
    checks['Writable program folder'] = os.access(ROOT, os.W_OK)
    for key, success in checks.items():
        print(('OK   ' if success else 'FAIL ') + key)
    print('Local source directory:', ROOT)
    print('Data directory (created at first run):', ROOT / 'data')
    print('Excel primary output: your Windows Downloads folder')
    return 0 if all(checks.values()) else 1

if __name__ == '__main__': sys.exit(main())
