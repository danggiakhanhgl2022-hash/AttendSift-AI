"""Prevent the flattened-upload failures observed in the public repository."""
from tools.check_repository_layout import problems


def test_official_layout_allows_real_entrypoints_and_nested_source():
    assert not problems(['README.md', 'app.py', 'main.py', '.github/workflows/ci.yml',
                         'cloud/app.py', 'src/app/__init__.py', 'tests/test_personnel.py',
                         'docs/README.md', 'docs/images/story/cover.png'])


def test_flattened_source_and_duplicate_readmes_are_rejected():
    for name in ['README (1).md', '__init__ (2).py', 'cloud.js', 'ci.yml',
                 'test_personnel.py', 'cover.png', 'download']:
        assert problems([name]), name


def test_tracked_python_cache_is_rejected_even_inside_source():
    assert problems(['tools/__pycache__/privacy_audit.cpython-311.pyc'])
