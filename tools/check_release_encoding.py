"""Validate UTF-8 and Vietnamese content in release documentation."""
from pathlib import Path
import re
import sys

VIETNAMESE_FILES = [
    "README.md", "CHANGELOG.md", "docs/INSTALL_WINDOWS.md",
    "docs/CHUYEN_MAY_WINDOWS.md", "docs/CLOUD_OPERATIONS.md",
    "docs/RETENTION_3_MONTHS.md", "docs/PUBLISH_1.0.2.md",
    "docs/RELEASE_NOTES_1.0.2.md", "docs/HANDOVER_ACCEPTANCE.md",
    "docs/COMMUNITY_REVIEW.md", "docs/TESTING.md",
    "docs/RELEASE_CHECKLIST.md", "docs/FEATURE_MATRIX.md",
    "docs/GITHUB_ABOUT_AND_CV.md", "docs/VERIFICATION_1.0.2.md",
    "docs/ARCHITECTURE.md",
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
        if "Chuy\u1ec3n b\u00e1o c\u00e1o Chatwork" not in readme:
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
