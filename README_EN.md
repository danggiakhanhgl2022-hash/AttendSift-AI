# ChamCongChatwork — Local-first Attendance from Chatwork

[Tiếng Việt](README.md) · [Windows setup](docs/INSTALL_WINDOWS.md) · [Architecture](docs/ARCHITECTURE.md) · [Testing status](docs/TESTING.md)

**Release Candidate — portfolio/technical demonstration, not a certified production release.** A Windows-local Python/Flask application that interprets semi-structured attendance reports in Chatwork messages, links extracted events to source messages, and exports a four-sheet Excel workbook.

![Redacted screenshot of the desktop UI](docs/images/01-local-interface-redacted.png)

> The screenshots are derived from actual application/Excel captures with employee records **opaquely redacted**. No private chat messages, employee spreadsheets or private demo footage are redistributed in this repository.

## Why it exists

Real-world messages often list several employees and several dates in one post. Attendance extraction should produce one event per employee/date/category, applying the stated overtime **to each mentioned person** rather than splitting it among them. The source record must remain auditable, and ambiguous claims must be reviewable.

## Implemented components (as observed in source)

- Chatwork message sync and local SQLite storage.
- AI provider adapters and rules-based source reconciliation.
- Multi-person, multi-date, multi-duration overtime extraction with source IDs.
- Source-only handling of annual-leave requests and explicitly labelled contractors `(CTV)` per current business policy.
- Review workflow for ambiguous/unsupported attendance interpretations.
- Four-sheet Excel output: source messages, detailed events, summary, review queue.
- Local Windows launch via browser / desktop webview and a Windows build workflow.

### Fictional scenario

A single fictional report contains **Lan 1h, Minh & Bình 2h** on Oct 5 and **Lan 1h30, Minh 30m, Nam 1h** on Oct 7. The result is **six independently linked overtime rows**, not a shared 2-hour pool.

## Run on another Windows PC

Requires Windows 10/11 x64, Python 3.11 x64, and Internet for initial dependencies plus live API calls.

1. Download repository ZIP and extract it to a writable folder.
2. Run `CAI_DAT_WINDOWS.bat`.
3. Run `CHAY_LOCAL_WINDOWS.bat` and visit `http://127.0.0.1:8766`.
4. Supply your own Chatwork/AI credentials in Settings; do not reuse encrypted credentials from another Windows account.

For a standalone EXE, build on Windows using `TAO_EXE_WINDOWS.bat` or GitHub Actions and **validate the binary on a clean Windows machine** before distributing it. GitHub Pages cannot host this Python backend. The optional `cloud/` variant requires separate infrastructure and is not needed for the local application.

## Evidence and important limits

Source compilation and selected unit/regression tests have been executed; **Windows desktop acceptance, live Chatwork/AI end-to-end tests, and Microsoft Excel compatibility have not been fully verified in this environment**. See [test methodology](docs/TESTING.md), [feature matrix](docs/FEATURE_MATRIX.md), and [release checklist](docs/RELEASE_CHECKLIST.md).

Use with synthetic data first. The project is not officially affiliated with Chatwork or AI vendors. This repository is **not automatically open-source licensed**; see [licensing decision](LICENSE_DECISION.md) before distributing/reusing code.
