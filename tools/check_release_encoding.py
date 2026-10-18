"""Validate UTF-8 and Vietnamese content in release documentation."""
from pathlib import Path
import re
import sys

VIETNAMESE_FILES = [
    "README.md", "CHANGELOG.md", "docs/INSTALL_WINDOWS.md",
    "docs/PRIVACY_AND_SECURITY.md", "docs/MAU_BAO_CAO_CHAM_CONG.md",
]


def validate(root):
    errors = []
    for name in VIETNAMESE_FILES:
        try:
            text = (Path(root) / name).read_text(encoding="utf-8-sig")
        except (UnicodeError, OSError):
            errors.append(name + ": missing file or invalid UTF-8")
            continue
        if "\ufffd" in text:
            errors.append(name + ": replacement character")
        if sum("\u00c0" <= char <= "\u1eff" for char in text) < 15:
            errors.append(name + ": missing expected Vietnamese characters")
        if re.search(r"[A-Za-z\u00c0-\u1eff]\?[A-Za-z\u00c0-\u1eff]", text):
            errors.append(name + ": possible lossy question-mark replacement")
    if not errors:
        readme = (Path(root) / "README.md").read_text(encoding="utf-8-sig")
        if "b\u1ea3ng ch\u1ea5m c\u00f4ng" not in readme:
            errors.append("README.md: expected Vietnamese introduction missing")
    return errors


def main():
    errors = validate(sys.argv[1] if len(sys.argv) > 1 else ".")
    for error in errors:
        print("FAIL:", error)
    if not errors:
        print(f"PASS: {len(VIETNAMESE_FILES)} documents preserve UTF-8 Vietnamese.")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
