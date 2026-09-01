# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-09-01

### Added

- Shamsi (Jalali/Persian) calendar date shown alongside the Gregorian date in the HTML report header (via `jdatetime`, optional dependency)

## [0.2.0] - 2026-09-01

### Added

- Interactive JS sort & filter toolbar in the HTML report: free-text search, and filters for priority, issue type and assignee
- Sorting by task name, key, priority, status, assignee or last-action time, with ascending/descending toggle
- Priority is now the default sort (highest first)
- Sub-tasks are grouped under their parent (the "original") task, and the parent is always included even when it has no activity of its own
- Accordion header now shows the last action performed by the user; the rest of the activity is shown inside the accordion content

## [0.1.0] - 2026-08-31

### Added

- Jira REST API integration with paginated issue search and changelog expansion
- Per-user filtering for field changes and comments
- Console output with ANSI color coding (redacted user names, timestamps, field diffs)
- Self-contained HTML report generation with RTL/Persian layout, accordion UI, and stat cards
- Interactive keyboard menu using `prompt_toolkit` (arrow/j/k navigation, Enter to select)
- CLI mode with flags: `--user`, `--date`, `--html`, `--base-url`, `--out-dir`, `--no-color`, `--menu`
- `.env`-based configuration via `python-dotenv`
- Multiple auth methods: Bearer PAT, username/password, API token
- HTML report archiving to `reports/` directory
- Auto-open HTML reports in Chrome/Chromium with fallback to default browser
- Settings editor in the interactive menu
- Past reports viewer in the interactive menu
