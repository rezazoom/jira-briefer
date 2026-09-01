# Changelog

All notable changes to this project will be documented in this file.

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
