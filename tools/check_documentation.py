"""Verify local links and illustrations in the current, consolidated documents."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
import re
ROOT=Path(__file__).resolve().parents[1]

def main():
    errors=[];count=0
    files=list(ROOT.glob('*.md'))+list((ROOT/'docs').rglob('*.md'))
    for file in files:
        text=file.read_text(encoding='utf-8-sig')
        links=re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)',text)+re.findall(r'<img\b[^>]*src=["\x27]([^"\x27]+)',text)
        for link in links:
            parsed=urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:continue
            count+=1;target=(file.parent/unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():errors.append(f'{file.relative_to(ROOT)}: missing {link}')
    if errors:raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(files)} current documents and {count} local links/assets.')
if __name__=='__main__':main()
