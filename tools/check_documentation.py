"""Check links/assets in the current public documentation, not historical reports."""
from pathlib import Path
from html.parser import HTMLParser
import re
import struct
import argparse
import subprocess
import unicodedata
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ['README.md', 'README_EN.md', 'CHANGELOG.md', 'docs/UPDATE_2026-10-16.md', 'docs/README.md', 'docs/PRODUCT_TOUR.md',
           'docs/PROMPT_GIOI_THIEU_GITHUB.md', 'docs/ARCHITECTURE.md',
           'docs/ARCHITECTURE_REVIEW_1.1.0.md', 'docs/FEATURE_MATRIX.md',
           'docs/BUSINESS_RULES.md', 'docs/TESTING.md', 'docs/PORTFOLIO_STORY.md',
           'docs/DEMO_GUIDE.md', 'docs/GITHUB_ABOUT_AND_CV.md', 'docs/BO_CUC_GIOI_THIEU_SAN_PHAM.md',
           'docs/images/story/README.md']


def anchors(content):
    found = set()
    for heading in re.findall(r'^#{1,6}\s+(.+)$', content, re.M):
        label = re.sub(r'<[^>]+>', '', heading).strip().lower()
        label = ''.join(c for c in label if c in '-_' or c.isspace()
                        or unicodedata.category(c)[0] in {'L', 'N'})
        found.add(re.sub(r'\s', '-', label))
    return found


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            data = dict(attrs)
            if not data.get('alt'):
                raise ValueError('HTML image needs alt text')
            self.links.append(data['src'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--git-ref', help='Also verify referenced images exist at this Git revision')
    args = parser.parse_args()
    remote_files = None
    if args.git_ref:
        remote_files = set(subprocess.check_output(
            ['git', '-C', str(ROOT), 'ls-tree', '-r', '--name-only', args.git_ref],
            text=True, encoding='utf-8').splitlines())
    files = [ROOT / name for name in CURRENT] + sorted((ROOT / 'docs/articles').glob('*.md'))
    errors, count = [], 0
    for file in files:
        content = file.read_text(encoding='utf-8-sig')
        parser = Images()
        parser.feed(content)
        links = re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)', content) + parser.links
        for link in links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (file.parent / unquote(parsed.path)).resolve() if parsed.path else file
            count += 1
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f'{file.relative_to(ROOT)}: missing target {link}')
            elif remote_files is not None and target.suffix.lower() in {'.png', '.jpg', '.svg'} and target.relative_to(ROOT).as_posix() not in remote_files:
                errors.append(f'{args.git_ref}: image not uploaded at {target.relative_to(ROOT).as_posix()}')
            elif parsed.fragment and target.suffix == '.md':
                if unquote(parsed.fragment) not in anchors(target.read_text(encoding='utf-8-sig')):
                    errors.append(f'{file.relative_to(ROOT)}: missing anchor {link}')
    assets = ROOT / 'docs/images/story'
    for svg in assets.glob('*.svg'):
        ElementTree.parse(svg)
    for png in assets.glob('*.png'):
        data = png.read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n', png.name
        width, height = struct.unpack('>II', data[16:24])
        assert width >= 1000 and height >= 600, png.name
    expected = [f'ui-{tab}.png' for tab in ['sync', 'export', 'history', 'settings', 'employees']]
    expected += ['01-source.png', '02-attendance.png', '03-summary.png', '04-review.png', '05-contractors.png']
    errors += [f'Missing public image: {name}' for name in expected if not (assets / name).is_file()]
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(files)} current documents, {count} local links, 10 product images and SVG assets.')


if __name__ == '__main__':
    main()
