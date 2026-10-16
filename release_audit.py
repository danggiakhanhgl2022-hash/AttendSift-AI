"""Fails CI if tracked files contain private runtime artifacts.

Run against a checkout; checks tracked files if Git is initialized, else directory files.
It does not print potentially sensitive file content.
"""
from pathlib import Path
import subprocess
import sys

BLOCKED_DIRS = {'data', 'outputs', 'output', 'backups', 'logs', 'config', '.venv', 'deploy/bundle'}
BLOCKED_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.credentials', '.exe', '.zip', '.csv', '.log', '.pyc', '.pyo'}


def main(path):
    root = Path(path).resolve()
    if not root.is_dir(): raise SystemExit('Not a directory')
    tracked = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], capture_output=True)
    if tracked.returncode == 0 and tracked.stdout:
        files = [root / n.decode('utf-8') for n in tracked.stdout.split(b'\0') if n]
    else:
        files = [p for p in root.rglob('*') if p.is_file()]
    errors = []
    for file in files:
        if file.name.startswith('NHAN_VIEN_RIENG'):
            errors.append(file.relative_to(root))
        parts = file.relative_to(root).parts
        if any(part in BLOCKED_DIRS for part in parts): errors.append(file.relative_to(root))
        if file.suffix.lower() in BLOCKED_SUFFIXES or file.name.startswith('.env.') and file.name != '.env.example' or file.name == '.env':
            errors.append(file.relative_to(root))
        if file.suffix.lower() == '.xlsx' and file.relative_to(root).as_posix() != 'templates/template.xlsx':
            errors.append(file.relative_to(root))
    if errors:
        print('Blocked files in release:')
        print('\n'.join(' - ' + str(p) for p in sorted(set(errors))))
        raise SystemExit(1)
    print(f'PASS: checked {len(files)} files; no forbidden runtime data or credential files.')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv)>1 else '.')
