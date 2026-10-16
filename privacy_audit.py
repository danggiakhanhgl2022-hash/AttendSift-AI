"""Best-effort public repository secret/artifact check. Does not replace manual review."""
from pathlib import Path
import re
import sys

BLOCKED_DIRS={'.git','data','outputs','output','backups','logs','config','.venv','venv','build','release','dist'}
BLOCKED_NAMES={'nhan_vien_rieng.json','.env','id_rsa','id_ed25519'}
BLOCKED_SUFFIXES={'.db','.sqlite','.sqlite3','.exe','.csv','.xls','.pfx','.p12','.pem','.key','.log','.zip'}
EXPOSED_PATTERNS=[
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'(?i)(?:(?:sk-proj-|sk-live-)[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{25,}|ghp_[0-9A-Za-z]{30,})'),
    re.compile(r'(?i)(?:postgresql?|mongodb(?:\+srv)?)://[^\s\"\x27]+:[^\s\"\x27]+@'),
    re.compile(r'(?i)https?://[^/\s\"\x27]+:[^@\s\"\x27]+@'),
]

def audit(root):
    errors=[]; files=0
    for file in root.rglob('*'):
        if not file.is_file(): continue
        rel=file.relative_to(root)
        # .git is repository metadata, not an artifact to stage or audit.
        if '.git' in rel.parts: continue
        if any(x in BLOCKED_DIRS for x in rel.parts) or file.name.casefold() in BLOCKED_NAMES or file.name.startswith('NHAN_VIEN_RIENG') or file.suffix.casefold() in BLOCKED_SUFFIXES or (file.name.startswith('.env.') and file.name!='.env.example') or (file.suffix=='.xlsx' and rel.as_posix()!='templates/template.xlsx'):
            errors.append(str(rel)+': blocked file')
            continue
        files+=1
        if file.stat().st_size > 1_000_000 or file.suffix.lower() not in {'.py','.md','.json','.yml','.yaml','.js','.html','.css','.txt','.example','.bat','.toml','.xml'}: continue
        try: data=file.read_text(encoding='utf-8')
        except UnicodeError: continue
        for pat in EXPOSED_PATTERNS:
            if pat.search(data):
                errors.append(str(rel)+': possible embedded secret')
                break
    return files, errors

if __name__=='__main__':
    count, errors=audit(Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve())
    for error in errors: print('FAIL',error)
    if errors: raise SystemExit(1)
    print('PASS:',count,'files audited for blocked paths and common secret patterns; manual review still required')
