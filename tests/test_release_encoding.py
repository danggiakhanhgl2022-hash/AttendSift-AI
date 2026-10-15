"""Catch UTF-8 files whose Vietnamese was lost before writing."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "release_encoding", ROOT / "tools/check_release_encoding.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_release_documentation_preserves_vietnamese():
    assert module.validate(ROOT) == []


@pytest.mark.parametrize("damage", ["lossy", "invalid_utf8", "replacement"])
def test_encoding_check_rejects_damaged_documents(tmp_path, monkeypatch, damage):
    monkeypatch.setattr(module, "VIETNAMESE_FILES", ["README.md"])
    original = (ROOT / "README.md").read_text(encoding="utf-8")
    if damage == "lossy":
        value = original.encode("ascii", errors="replace")
    elif damage == "invalid_utf8":
        value = b"\xff\xfe\xfa"
    else:
        value = (original + "\ufffd").encode("utf-8")
    (tmp_path / "README.md").write_bytes(value)
    assert module.validate(tmp_path)
