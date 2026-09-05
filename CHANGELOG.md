# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-09-05

### Added

- Issue keys and summaries in the HTML report now link to the original Jira task (`{base_url}/browse/{KEY}`), opening in a new tab, for both parent tasks and sub-tasks
- Arad variable font (v1.0.1, SIL OFL 1.1) is now embedded as a base64 data URI in the HTML template, so reports render in Arad on any machine — no local font install needed

### Fixed

- The interactive menu no longer wipes Jira auth tokens from `.env` when changing settings/output format; existing `JIRA_TOKEN`, `JIRA_PASSWORD`, and `JIRA_API_TOKEN` values are preserved

### Changed

- Interactive menu now clears the terminal on startup and before exiting

## [0.3.0] - 2026-09-01

### Changed

- Bumped CI actions to Node 24 versions (`actions/checkout@v5`, `actions/setup-python@v6`)
- Removed internal `jira.rahbal.site` default and `r.esmaeili` username from the source and docs; the base URL is now required via `.env` or `--base-url`, with a clear error when missing
- Rewrote repository history to scrub internal URLs/identifiers and force-pushed to both remotes
- Cleaned up unused imports and variables flagged by Pylint

### Added

- Pylint code quality check via GitHub Actions (`.github/workflows/lint.yml`)
- Pragmatic `.pylintrc` configuration tailored to the single-file, lazy-import architecture

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
