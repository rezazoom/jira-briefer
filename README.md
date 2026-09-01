# Jira Daily Briefer

A personal CLI tool that generates daily activity reports from Jira. It queries the Jira REST API to find all issues a user touched on a given day and lists their field changes and comments.

## Features

- **Jira Activity Tracking** — Finds all issues updated on a target date (default: yesterday) with full changelog
- **Per-User Filtering** — Shows only changes and comments made by the specified user
- **Two Output Formats:**
  - **Console** — Color-coded plain-text report grouped by issue
  - **HTML** — Self-contained, styled, RTL/Persian report with accordion UI and stat cards
- **Interactive Keyboard Menu** — Navigate with arrow keys, j/k, Enter
- **Report Archive** — Saves generated HTML reports to `reports/` directory

## Prerequisites

- Python 3.7+
- A Jira account with a Personal Access Token (PAT)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd ava-jira-briefer

# Install dependencies
pip install requests python-dotenv prompt_toolkit jdatetime

# Configure credentials
cp .env.example .env
# Edit .env and fill in your JIRA_USERNAME and JIRA_TOKEN
```

### Getting a Jira PAT

1. Log in to Jira
2. Click your avatar → **Profile** → **Personal Access Tokens**
3. Click **Create token** and copy it

## Usage

### Interactive Menu (default)

```bash
python3 jira-briefer.py
```

Use arrow keys or `j`/`k` to navigate, `Enter` to select.

### CLI Mode

```bash
# Report for a specific user and date
python3 jira-briefer.py --user <your-username> --date 2026-08-31

# Generate HTML report
python3 jira-briefer.py --html

# Use a custom Jira instance
python3 jira-briefer.py --base-url https://jira.example.com

# Combine flags
python3 jira-briefer.py --user <your-username> --date 2026-08-31 --html
```

### CLI Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--user` | Jira username | From `.env` or `<your-username>` |
| `--date` | Target date (`YYYY-MM-DD`) | Yesterday |
| `--html` | Output as HTML instead of console | `console` |
| `--base-url` | Jira server URL | From `.env` or `https://jira.example.com` |
| `--out-dir` | Directory for HTML reports | `./reports` |
| `--no-color` | Disable ANSI colors in console output | Colors enabled |
| `--menu` | Force the interactive menu | — |

## Configuration

All settings are stored in `.env`:

```env
JIRA_USERNAME=<your-username>
JIRA_TOKEN=your_personal_access_token
JIRA_BASE_URL=https://jira.example.com
JIRA_OUTPUT_FORMAT=console
```

## Project Structure

```
├── jira-briefer.py    # Main application (API, menu, report generation)
├── template.html      # HTML report template (RTL/Persian)
├── .env.example       # Template for credentials
├── .env               # Your actual credentials (gitignored)
├── .gitignore
└── reports/           # Generated HTML reports (gitignored)
```

## License

Personal use.
