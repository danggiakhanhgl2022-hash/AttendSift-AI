# AttendSift AI

**Turn Chatwork reports into attendance records that can be reviewed against their source.**

AI Department | Dang Gia Khanh | Version 1.0.2

[Vietnamese documentation](README.md) ? [Windows setup](docs/INSTALL_WINDOWS.md) ? [Verification](docs/VERIFICATION_1.0.2.md)

AttendSift AI stores source messages, uses an AI provider to assist with event extraction, applies business rules, and lets an operator review the results before exporting a four-sheet Excel workbook. It handles messages mentioning multiple people and dates, with separate overtime amounts for each person.

## Deployment options

| | Windows Local | Cloud website |
|---|---|---|
| Storage | Per-installation SQLite | Neon PostgreSQL |
| Launch | Portable EXE or Python source | Browser with authentication |
| Scheduling | Windows Task Scheduler | Vercel Cron |
| Automatic retention | Cloud policy does not apply | Three calendar months |

These deployments do not automatically share data or API credentials. Local processing still sends relevant content to the configured AI service. Internet access and API quota are required for remote operations.

## Windows quick start

For a verified portable bundle, extract the entire ZIP, read `DOC_TRUOC_KHI_CHAY.html`, run `KIEM_TRA.bat`, then `BAT_DAU.bat`. The target machine does not need Python. Enter the recipient's Chatwork and AI credentials; do not transfer Windows-encrypted credentials from another account.

For source installation, use Python 3.11 x64 and run `CAI_DAT_WINDOWS.bat`, `KIEM_TRA_LOCAL_WINDOWS.bat`, then `CHAY_LOCAL_WINDOWS.bat`. The default address is `http://127.0.0.1:8766`. Source ZIPs do not contain a prebuilt EXE.

## Version 1.0.2

- Refresh cloud messages after synchronization and improve filter feedback.
- Display cloud message timestamps in Vietnam time with an unbroken date/time string.
- Authenticate cron independently of a rotating deployment hostname, only on its exact endpoint.
- Remove expired cloud messages, analysis sessions, reports and activity history during authorized daily cron runs; keep connection settings.
- Consolidate setup, handoff, release and operations documentation.

Messages expire three calendar months after sending. Analysis sessions and their source snapshots/results/Excel expire three months after session creation. Download reports needed for long-term storage before expiry. Retention does not guarantee that three months of usage will fit a free hosting plan.

## Validation and limitations

This is an internal release candidate. See the verification report for measured results and remaining acceptance tasks. Chatwork's recent-message window may omit earlier history. AI results require human review. Clean-machine Windows acceptance, live provider validation and Microsoft Excel checks must be recorded separately.

No open-source license has been granted; see [LICENSE_DECISION.md](LICENSE_DECISION.md). Keep credentials, employee data and runtime databases out of public uploads. Report issues using synthetic examples through the repository's contribution and security guidance.
