# CLAUDE.md

Instructions for AI assistants working on this codebase.

## Project Overview

Jira Daily Briefer — a single-file Python CLI tool (`jira-briefer.py`, ~617 lines) that generates daily activity reports from Jira. Queries the Jira REST API, filters changes/comments by user, and outputs to console (colored text) or HTML (RTL/Persian accordion report).

## Architecture

- **`jira-briefer.py`** — Monolithic script containing all logic:
  - Config loading from `.env` via `python-dotenv`
  - Jira API calls (`requests`): paginated search, changelog expansion, comment fetching
  - User filtering for changelog histories and comments
  - Console renderer with ANSI escape codes
  - HTML renderer using token replacement on `template.html`
  - Interactive menu using `prompt_toolkit`
  - CLI argument parsing with `argparse`
  - Browser opening logic (Chrome/Chromium fallback)
- **`template.html`** — Jinja-style template with `{{__TOKENS__}}` placeholders for HTML report generation. RTL/Persian layout with Vazirmatn/Arad fonts.

## Key Conventions

- Single-file architecture — keep all logic in `jira-briefer.py`
- No test framework is currently set up
- No linter/formatter is configured
- Comments and UI text are a mix of English and Persian (Farsi)
- HTML reports are designed for RTL (right-to-left) Persian text
- Config is stored in `.env` (never commit real `.env`)
- Generated reports go to `reports/` (gitignored)

## Development

```bash
# Run the tool
python3 jira-briefer.py

# Run with CLI flags (skips menu)
python3 jira-briefer.py --user <your-username> --date 2026-08-31 --html
```

## Dependencies

- `requests` — HTTP client for Jira API
- `python-dotenv` — `.env` file loading (optional, gracefully skipped if missing)
- `prompt_toolkit` — Interactive keyboard menu
- `jdatetime` — Shamsi (Jalali) date conversion for the HTML report (optional, gracefully skipped if missing)

## Common Tasks

- **Adding a new CLI flag:** Add to the `argparse` section (~line 500) and wire it into `cmd_cli()` and `run_menu()`
- **Adding a new Jira field:** Update the `fields` parameter in `fetch_all_issues()` and add rendering in `render_console()` / `render_html()`
- **Modifying HTML output:** Edit `template.html` and update the token replacement in `render_html()`
- **Changing default config:** Update `DEFAULT_BASE_URL`, `DEFAULT_USER`, or the `.env` loading logic near the top of the file

## Security

- Never commit `.env` — it contains Jira PAT tokens
- The tool supports multiple auth methods but `.env` is the primary config source
