# AttendSift AI

**Turn Chatwork reports into attendance records that can be reviewed against their source.**

![AttendSift AI overview](docs/images/story/cover.svg)

AI Department | Dang Gia Khanh | Version 1.1.0

[Vietnamese documentation](README.md) · [Windows setup](docs/INSTALL_WINDOWS.md) · [Verification](docs/VERIFICATION_1.1.0.md)

## Product, workflow and engineering story

The repository contains both Windows Local and the Cloud backend. Local uses a web interface inside WebView2 or a loopback browser; it does not share its SQLite data or credentials automatically with the Cloud PostgreSQL deployment.

![Local interface with synthetic data](docs/images/story/ui-sync.png)

This screenshot shows the actual Local application running against a temporary demo database. All people, messages and room information are fictional. It is not evidence of a deployed Cloud instance.

Five tabs organize the work: synchronization, attendance export, history, settings and employees. A session captures the roster and source context. AI suggests events, source reconciliation and validation check them, and unresolved rows remain outside payroll totals until reviewed.

![Synthetic workbook summary](docs/images/story/03-summary.png)

The workbook provides five views: original messages, official employee events, official totals, review items and contractors. These illustrations are rendered from values exported by the application, not screenshots or acceptance results from Microsoft Excel or WPS.

| Read more | Focus |
|---|---|
| [Product tour](docs/PRODUCT_TOUR.md) | All five tabs and worksheets, with image provenance |
| [Architecture](docs/ARCHITECTURE.md) | People, external systems, deployments and module responsibilities |
| [Six articles](docs/articles/README.md) | User workflow, AI evidence, Excel handoff, Local/Cloud, trade-offs and verification |
| [Source review](docs/ARCHITECTURE_REVIEW_1.1.0.md) | InfoQ, Stack Overflow Blog, C4, Diátaxis and GitHub Docs; selected ideas and limitations |
| [Current verification](docs/UPDATE_2026-10-16.md) | 398 Python tests passed on the recorded Windows environment; separate live acceptance still required |

The architecture keeps a deployable application divided into modules for each environment. Shared policy reduces divergence, but two orchestration/storage paths still require regression checks. Snapshots improve explainability and cost storage; Excel eases handoff and creates copy/version responsibilities. No forum ranking or endorsement is claimed.

AttendSift AI stores source messages, uses an AI provider to assist with event extraction, applies business rules, and lets an operator review the results before exporting a five-sheet Excel workbook. It handles messages mentioning multiple people and dates, with separate overtime amounts for each person.

## Update: 16 October 2026

The existing Local/Cloud features remain available. This update adds a source-verified 30-minute paid early departure, improves roster matching, and allows Excel export while unresolved rows remain in the review worksheet.

- Only an explicit request by the person concerned for 30 minutes of early departure without make-up work qualifies. Count reported dates only; do not fill missing dates.
- Paid minutes do not increase unpaid minutes, OT, or leave days. The workbook adds column AB in attendance, O in the summary, and L in contractor reporting.
- Resolve full names, unique given names, middle-name suffixes and registered aliases against the active roster. Ambiguous identities and conflicting evidence stay out of totals.
- Export first, inspect worksheet 4, then reopen the session to correct and confirm records before exporting again.
- Ordinary leave and annual-leave requests remain in source messages; do not automatically calculate leave days from AI guesses.

See the [paid-break policy](docs/CHINH_SACH_NGHI_30_PHUT_CO_LUONG.md) and [current verification](docs/UPDATE_2026-10-16.md). New analysis sessions use the updated rules; Windows executables must be rebuilt separately.

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

## Version 1.1.0

- Refresh cloud messages after synchronization and improve filter feedback.
- Display cloud message timestamps in Vietnam time with an unbroken date/time string.
- Authenticate cron independently of a rotating deployment hostname, only on its exact endpoint.
- Remove expired cloud messages, analysis sessions, reports and activity history during authorized daily cron runs; keep connection settings.
- Consolidate setup, handoff, release and operations documentation.

Messages expire three calendar months after sending. Analysis sessions and their source snapshots/results/Excel expire three months after session creation. Download reports needed for long-term storage before expiry. Retention does not guarantee that three months of usage will fit a free hosting plan.

## Validation and limitations

This is an internal release candidate. See the verification report for measured results and remaining acceptance tasks. Chatwork's recent-message window may omit earlier history. AI results require human review. Clean-machine Windows acceptance, live provider validation and Microsoft Excel checks must be recorded separately.

No open-source license has been granted; see [LICENSE_DECISION.md](LICENSE_DECISION.md). Keep credentials, employee data and runtime databases out of public uploads. Report issues using synthetic examples through the repository's contribution and security guidance.

## Personnel update

Version 1.1.0 adds employee management, immutable roster snapshots per session and separate contractor reporting in a fifth worksheet. The October update keeps ordinary leave source-only and adds paid-break reporting. Private employee bootstrap data is distributed separately from public source. Ambiguous or conflicting identities require review. Existing session snapshots remain available in history.
