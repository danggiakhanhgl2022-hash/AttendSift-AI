"""Reject flattened uploads and duplicate files in the repository root."""
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    '.env.example', '.gitattributes', '.gitignore', '.python-version',
    'README.md', 'README_EN.md', 'CHANGELOG.md', 'CONTRIBUTING.md',
    'SECURITY.md', 'LICENSE_DECISION.md', 'VERSION', 'app.py', 'main.py',
    'ChamCong.spec', 'pytest.ini', 'vercel.json', 'build.bat',
    'CAI_DAT_WINDOWS.bat', 'CHAY_LOCAL_WINDOWS.bat',
    'KIEM_TRA_LOCAL_WINDOWS.bat', 'TAO_EXE_WINDOWS.bat',
    'requirements.txt', 'requirements-build.txt', 'requirements-desktop.txt',
    'requirements-dev.txt', 'requirements-local.txt',
    'requirements-ui-test.txt', 'requirements-web.txt',
}
ROOT_DIRS = {'.github', 'cloud', 'docs', 'public', 'src', 'static',
             'templates', 'tests', 'tools'}


def problems(paths):
    errors = []
    for name in paths:
        path = PurePosixPath(name)
        if len(path.parts) == 1 and name not in ROOT_FILES:
            errors.append(name + ': unexpected root file; preserve its source directory')
        elif len(path.parts) > 1 and path.parts[0] not in ROOT_DIRS:
            errors.append(name + ': unexpected top-level directory')
        if '__pycache__' in path.parts or path.suffix in {'.pyc', '.pyo'}:
            errors.append(name + ': generated cache must not be tracked')
    return errors


if __name__ == '__main__':
    paths = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode('utf-8').split('\0')
    errors = problems(p for p in paths if p)
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS: official repository layout; no flattened uploads or tracked caches.')
