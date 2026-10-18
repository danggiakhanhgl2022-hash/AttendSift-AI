"""Copy the shared Neural Terminal assets to Flask and Vercel delivery paths."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ASSETS = (
    'cinematic.js', 'technology.css', 'technology-poster.png',
    'dashboard.css', 'dashboard.js', 'operation-orb.css', 'operation-orb.js',
    'panel-motion.css', 'panel-motion.js', 'people-summary.css', 'people-summary.js',
    'reference-console.css', 'reference-console.js',
)


def main():
    for name in ASSETS:
        for target in ('cloud/static', 'public/static'):
            shutil.copyfile(ROOT / 'static' / name, ROOT / target / name)
    shutil.copyfile(ROOT / 'cloud/static/neural-cloud.js', ROOT / 'public/static/neural-cloud.js')
    print('Shared Neural Terminal assets synchronized for Flask and Vercel.')


if __name__ == '__main__':
    main()
