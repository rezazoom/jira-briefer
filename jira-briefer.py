#!/usr/bin/env python3
"""
Jira Daily Briefer — گزارش فعالیت‌های روزانه شما در Jira

Runs an interactive keyboard menu by default:
    python3 jira-briefer.py

Or pass CLI flags directly (menu is skipped):
    python3 jira-briefer.py --user <your-username> --date 2026-08-31
    python3 jira-briefer.py --html
    python3 jira-briefer.py --base-url https://jira.example.com
"""

import requests
import json
import argparse
import os
import sys
import html
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# ─── Config ───────────────────────────────────────────────────────────────────
# Load .env from the script's directory
base_dir = Path(__file__).resolve().parent
if load_dotenv:
    load_dotenv(base_dir / ".env")

DEFAULT_BASE_URL = "https://jira.example.com"
DEFAULT_USER = os.getenv("JIRA_USERNAME", "<your-username>")

BOLD = "\033[1m"
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"


# ─── Helpers ──────────────────────────────────────────────────────────────────
def jql_date_filter(target_date: datetime) -> str:
    """Build JQL date range for a given day (start to end)."""
    start = target_date.strftime("%Y-%m-%d")
    end = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
    return f'updated >= "{start}" AND updated < "{end}"'


def fetch_all_issues(session: requests.Session, base_url: str, jql: str) -> list:
    """Paginate through /rest/api/2/search and return all matching issues."""
    url = f"{base_url}/rest/api/2/search"
    all_issues = []
    start_at = 0
    max_results = 50

    while True:
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "expand": "changelog",
            "fields": "summary,status,assignee,priority,issuetype,project",
        }
        resp = session.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        issues = data.get("issues", [])
        all_issues.extend(issues)
        total = data.get("total", 0)
        start_at += len(issues)
        if start_at >= total or not issues:
            break

    return all_issues


def fetch_comments(session: requests.Session, base_url: str, issue_key: str) -> list:
    """Fetch all comments for an issue (paginated)."""
    url = f"{base_url}/rest/api/2/issue/{issue_key}/comment"
    all_comments = []
    start_at = 0
    max_results = 50

    while True:
        params = {"startAt": start_at, "maxResults": max_results}
        resp = session.get(url, params=params)
        if resp.status_code == 404:
            break
        resp.raise_for_status()
        data = resp.json()
        comments = data.get("comments", [])
        all_comments.extend(comments)
        total = data.get("total", 0)
        start_at += len(comments)
        if start_at >= total or not comments:
            break

    return all_comments


def filter_changelog_by_user(changelog: dict, username: str) -> list:
    """Extract changelog histories made by the given user."""
    results = []
    for history in changelog.get("histories", []):
        author = history.get("author", {})
        if author.get("name", "") == username or author.get("emailAddress", "") == username:
            created = history.get("created", "")
            for item in history.get("items", []):
                field = item.get("field", "unknown")
                from_val = item.get("fromString") or "(empty)"
                to_val = item.get("toString") or "(empty)"
                results.append({
                    "type": "field_change",
                    "field": field,
                    "from": from_val,
                    "to": to_val,
                    "timestamp": created,
                })
    return results


def filter_comments_by_user(comments: list, username: str) -> list:
    """Extract comments made by the given user."""
    results = []
    for comment in comments:
        author = comment.get("author", {})
        if author.get("name", "") == username or author.get("emailAddress", "") == username:
            created = comment.get("created", "")
            body = comment.get("body", "")
            # Truncate long comments
            if len(body) > 200:
                body = body[:200] + "..."
            results.append({
                "type": "comment",
                "body": body,
                "timestamp": created,
            })
    return results


def format_timestamp(ts: str) -> str:
    """Format ISO timestamp to HH:MM."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")
    except Exception:
        return ts[:16] if len(ts) >= 16 else ts


# ─── HTML Report ──────────────────────────────────────────────────────────────
def esc(text):
    return html.escape(str(text), quote=True)


def generate_html(date_str, user, active_issues, total_field_changes, total_comments):
    """Build a self-contained HTML report with accordion boxes."""
    def priority_class(priority):
        p = (priority or "").lower()
        if "highest" in p or "critical" in p:
            return "prio-highest"
        if "high" in p:
            return "prio-high"
        if "low" in p or "lowest" in p:
            return "prio-low"
        return "prio-medium"

    report_date = date_str
    try:
        report_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A %d %B %Y")
    except Exception:
        pass

    items_html = []
    for i, (key, summary, status, priority, issuetype, assignee, activities) in enumerate(active_issues):
        acts_html = []
        for act in activities:
            ts = format_timestamp(act["timestamp"])
            if act["type"] == "field_change":
                acts_html.append(
                    f'<div class="act"><span class="ts">{ts}</span>'
                    f'<span class="badge badge-field">{esc(act["field"])}</span>'
                    f'<span class="from">{esc(act["from"])}</span>'
                    f'<span class="arrow">→</span>'
                    f'<span class="to">{esc(act["to"])}</span></div>'
                )
            elif act["type"] == "comment":
                body = esc(act["body"]).replace("\n", "<br>")
                acts_html.append(
                    f'<div class="act"><span class="ts">{ts}</span>'
                    f'<span class="badge badge-comment">Comment</span>'
                    f'<span class="comment-body">{body}</span></div>'
                )

        items_html.append(f"""
      <div class="acc-item">
        <div class="acc-head" data-acc="{i}">
          <span class="acc-arrow">▶</span>
          <span class="key">{esc(key)}</span>
          <span class="type">{esc(issuetype)}</span>
          <span class="prio {priority_class(priority)}">{esc(priority)}</span>
          <span class="acc-title">{esc(summary)}</span>
        </div>
        <div class="acc-body" id="acc-body-{i}">
          <div class="meta">Status: <b>{esc(status)}</b> &nbsp;|&nbsp; Assignee: <b>{esc(assignee)}</b></div>
          {"".join(acts_html)}
        </div>
      </div>""")

    page = "".join(items_html)

    template_path = base_dir / "template.html"
    template = template_path.read_text(encoding="utf-8")

    # Simple token replacement (CSS braces in the template stay literal).
    replacements = {
        "{{__USER__}}": esc(user),
        "{{__DATE__}}": esc(date_str),
        "{{__REPORT_DATE__}}": esc(report_date),
        "{{__NUM_ISSUES__}}": str(len(active_issues)),
        "{{__FIELD_CHANGES__}}": str(total_field_changes),
        "{{__COMMENTS__}}": str(total_comments),
        "{{__ITEMS__}}": page,
        "{{__GEN_AT__}}": esc(datetime.now().strftime("%Y-%m-%d %H:%M")),
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    return template


def open_in_browser(path):
    """Open a file in Chrome; fall back to the default browser."""
    try:
        subprocess.Popen(["google-chrome", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception:
        pass
    try:
        subprocess.Popen(["chromium", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception:
        pass
    webbrowser.open("file://" + path)


# ─── Report Core ──────────────────────────────────────────────────────────────
def build_session(username):
    """Create an authenticated requests.Session from .env values."""
    session = requests.Session()
    token = os.getenv("JIRA_TOKEN")
    password = os.getenv("JIRA_PASSWORD")
    api_token = os.getenv("JIRA_API_TOKEN")
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    elif password:
        session.auth = (username, password)
    elif api_token:
        session.auth = (username, api_token)
    return session, (bool(token) or bool(password) or bool(api_token))


def gather_activity(session, base_url, username, target_date):
    """Fetch + filter all activity for a user on a given day.

    Returns (date_str, active_issues, total_field_changes, total_comments)
    """
    date_str = target_date.strftime("%Y-%m-%d")
    jql = jql_date_filter(target_date)

    issues = fetch_all_issues(session, base_url, jql)

    total_field_changes = 0
    total_comments = 0
    active_issues = []

    for issue in issues:
        key = issue["key"]
        summary = issue["fields"].get("summary", "")
        status = issue["fields"].get("status", {}).get("name", "?")
        priority = issue["fields"].get("priority", {}).get("name", "?")
        issuetype = issue["fields"].get("issuetype", {}).get("name", "?")
        assignee_obj = issue["fields"].get("assignee")
        assignee = assignee_obj.get("displayName", "Unassigned") if assignee_obj else "Unassigned"

        changelog = issue.get("changelog", {})
        field_changes = filter_changelog_by_user(changelog, username)

        try:
            comments = fetch_comments(session, base_url, key)
        except Exception:
            comments = []
        user_comments = filter_comments_by_user(comments, username)

        all_activity = field_changes + user_comments
        if not all_activity:
            continue

        all_activity.sort(key=lambda x: x.get("timestamp", ""))

        total_field_changes += len(field_changes)
        total_comments += len(user_comments)
        active_issues.append((key, summary, status, priority, issuetype, assignee, all_activity))

    return date_str, active_issues, total_field_changes, total_comments


def print_report(date_str, username, active_issues, total_field_changes, total_comments,
                 colors=True):
    """Print a plain-text console report."""
    BOLD = RED = GREEN = YELLOW = CYAN = RESET = DIM = ""
    if colors:
        BOLD = "\033[1m"
        RED = "\033[91m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        CYAN = "\033[96m"
        DIM = "\033[2m"
        RESET = "\033[0m"

    print(f"\n{BOLD}{CYAN}═══════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{CYAN}  Jira Brief — {username} — {date_str}{RESET}")
    print(f"{BOLD}{CYAN}═══════════════════════════════════════════════{RESET}\n")

    for key, summary, status, priority, issuetype, assignee, activities in active_issues:
        print(f"{BOLD}{GREEN}  {key}{RESET}  {DIM}({issuetype}){RESET}  [{priority}]")
        print(f"  {summary}")
        print(f"  Status: {status}  |  Assignee: {assignee}")
        print(f"  {'─' * 44}")

        for act in activities:
            ts = format_timestamp(act["timestamp"])
            if act["type"] == "field_change":
                print(f"    {DIM}{ts}{RESET}  {BOLD}Field:{RESET}  {YELLOW}{act['field']}{RESET}")
                print(f"              {DIM}{act['from']}{RESET}  →  {GREEN}{act['to']}{RESET}")
            elif act["type"] == "comment":
                print(f"    {DIM}{ts}{RESET}  {BOLD}Comment:{RESET}")
                body_lines = act["body"].split("\n")
                for line in body_lines[:3]:
                    print(f"              {DIM}{line}{RESET}")
                if len(body_lines) > 3:
                    print(f"              {DIM}...{RESET}")
        print()

    print(f"{BOLD}{CYAN}═══════════════════════════════════════════════{RESET}")
    print(f"  {BOLD}Summary{RESET}")
    print(f"  Issues:   {BOLD}{len(active_issues)}{RESET}")
    print(f"  Changes:  {BOLD}{total_field_changes}{RESET} field change(s)")
    print(f"  Comments: {BOLD}{total_comments}{RESET}")
    print(f"{BOLD}{CYAN}═══════════════════════════════════════════════{RESET}\n")


def write_html_report(date_str, username, active_issues, total_field_changes,
                      total_comments, out_dir=None):
    """Write the HTML report to disk and return its path."""
    page = generate_html(date_str, username, active_issues,
                         total_field_changes, total_comments)
    out_path = Path(out_dir) if out_dir else Path.cwd()
    out_path.mkdir(parents=True, exist_ok=True)
    file_path = out_path / f"jira-brief-{username}-{date_str}.html"
    file_path.write_text(page, encoding="utf-8")
    return str(file_path)


def run_report(base_url, username, target_date, html=False, out_dir=None, colors=True):
    """Gather and output a report for a given date. Returns a status string."""
    session, authed = build_session(username)
    if not authed:
        print(f"{YELLOW}⚠  Warning: no JIRA_TOKEN/PASSWORD/API_TOKEN in .env — "
              f"continuing anonymously.{RESET}" if colors else
              "Warning: no auth found in .env — continuing anonymously.")
    print(f"{DIM}Fetching issues...{RESET}" if colors else "Fetching issues...")

    try:
        date_str, active_issues, tfc, tc = gather_activity(
            session, base_url, username, target_date)
    except requests.exceptions.RequestException as e:
        print(f"{RED}Error connecting to Jira: {e}{RESET}" if colors else f"Error: {e}")
        return "error"

    if html:
        path = write_html_report(date_str, username, active_issues, tfc, tc, out_dir)
        print(f"{GREEN}Saved: {path}{RESET}" if colors else f"Saved: {path}")
        open_in_browser(path)
    else:
        print_report(date_str, username, active_issues, tfc, tc, colors=colors)

    return "ok"


# ─── Interactive Menu ─────────────────────────────────────────────────────────
REPORT_DIR = base_dir / "reports"


def menu_choose(options, title):
    """A single-select keyboard menu using prompt_toolkit.

    Navigation: arrows / j / k. Select: Enter or Space. Cancel: Ctrl+C / Esc.
    Returns the index of the chosen option, or None if cancelled.
    """
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import Window, HSplit
    from prompt_toolkit.layout.controls import FormattedTextControl

    position = [0]
    result = [None]

    def render_title():
        return [("bold", f"{title}\n\n")]

    def render_menu():
        lines = []
        for i, (label, desc) in enumerate(options):
            cursor = "❯" if i == position[0] else " "
            style = "class:selected" if position[0] == i else ""
            text = f" {cursor} {label}"
            if desc:
                text += f"   {desc}"
            lines.append((style, text + "\n"))
        return lines

    kb = KeyBindings()

    @kb.add("up")
    @kb.add("k")
    def up(event):
        position[0] = (position[0] - 1) % len(options)

    @kb.add("down")
    @kb.add("j")
    def down(event):
        position[0] = (position[0] + 1) % len(options)

    @kb.add("enter")
    @kb.add("space")
    def select(event):
        result[0] = position[0]
        event.app.exit()

    @kb.add("c-c")
    @kb.add("escape")
    @kb.add("c-d")
    def cancel(event):
        event.app.exit()

    body = Window(FormattedTextControl(render_menu), height=len(options) + 1)
    root = HSplit([
        Window(FormattedTextControl(render_title), height=2),
        body,
    ])

    app = Application(layout=Layout(root), key_bindings=kb, full_screen=False)
    app.run()

    return result[0]


# ─── CLI / Entry ──────────────────────────────────────────────────────────────
def cmd_cli(argv):
    parser = argparse.ArgumentParser(description="Jira Daily Briefer")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Jira base URL")
    parser.add_argument("--user", default=DEFAULT_USER, help="Jira username to filter")
    parser.add_argument("--date", default=None, help="Target date (YYYY-MM-DD), default=yesterday")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("--html", action="store_true",
                        help="Generate and open an HTML report instead of console text")
    parser.add_argument("--out-dir", default=None, help="Directory to save the HTML report")
    args = parser.parse_args(argv)

    target_date = datetime.now() - timedelta(days=1)
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")

    run_report(args.base_url, args.user, target_date,
               html=args.html, out_dir=args.out_dir, colors=not args.no_color)


def run_menu():
    """Endless interactive menu loop."""
    from prompt_toolkit import prompt
    from prompt_toolkit.shortcuts import message_dialog, input_dialog

    # Load current config from .env
    username = os.getenv("JIRA_USERNAME", DEFAULT_USER)
    base_url = os.getenv("JIRA_BASE_URL", DEFAULT_BASE_URL)
    output_format = os.getenv("JIRA_OUTPUT_FORMAT", "console")  # console | html

    def save_config():
        lines = [
            "# Jira credentials — generated by jira-briefer menu",
            "",
            f"JIRA_USERNAME={username}",
            f"JIRA_BASE_URL={base_url}",
            f"JIRA_OUTPUT_FORMAT={output_format}",
        ]
        (base_dir / ".env").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def default_date():
        return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    def recent_reports():
        if not REPORT_DIR.is_dir():
            return []
        return sorted(REPORT_DIR.glob("jira-brief-*.html"), reverse=True)

    while True:
        print(f"\n┌─────────────────────────────────────────────")
        print(f"│  {BOLD}Jira Daily Briefer{RESET}")
        print(f"│  User: {username}   Base: {base_url}   Out: {output_format}")
        print(f"└─────────────────────────────────────────────\n")

        choices = [
            ("Run briefer (yesterday)", f"Generate report for {default_date()}"),
            ("Pick a specific date", "Choose which day to report on"),
            ("Output format", f"Currently: {output_format}"),
            ("Settings / config", f"User: {username} · Base URL · token check"),
            ("View past reports", f"{len(recent_reports())} HTML report(s) saved"),
            ("Exit", ""),
        ]
        idx = menu_choose(choices, "")

        if idx is None:
            print("\nBye!")
            return

        # 0: Run briefer (yesterday)
        if idx == 0:
            run_report(base_url, username, datetime.now() - timedelta(days=1),
                       html=(output_format == "html"), out_dir=str(REPORT_DIR))
            input("\nPress Enter to continue...")

        # 1: Pick a specific date
        elif idx == 1:
            date_input = prompt("Enter date (YYYY-MM-DD): ", default=default_date())
            try:
                target = datetime.strptime(date_input.strip(), "%Y-%m-%d")
            except ValueError:
                input("Invalid date. Press Enter...")
                continue
            run_report(base_url, username, target,
                       html=(output_format == "html"), out_dir=str(REPORT_DIR))
            input("\nPress Enter to continue...")

        # 2: Output format
        elif idx == 2:
            fmt_choices = [
                ("Console (text)", "Plain report in the terminal"),
                ("HTML", "Accordion report opened in Chrome"),
            ]
            f_idx = menu_choose(fmt_choices, "Output format")
            if f_idx is not None:
                output_format = "html" if f_idx == 1 else "console"
                save_config()
                print(f"\nOutput format set to: {output_format}")

        # 3: Settings
        elif idx == 3:
            new_user = input_dialog(
                title="Settings",
                text="Jira username:",
                default=username,
            ).run()
            if new_user:
                username = new_user.strip() or username
            new_url = input_dialog(
                title="Settings",
                text="Jira base URL:",
                default=base_url,
            ).run()
            if new_url:
                base_url = new_url.strip() or base_url

            token_set = bool(os.getenv("JIRA_TOKEN") or os.getenv("JIRA_PASSWORD")
                             or os.getenv("JIRA_API_TOKEN"))
            print(f"\nAuth from .env: {'configured ✓' if token_set else 'MISSING (anon)'}")
            save_config()
            input("Press Enter to continue...")

        # 4: View past reports
        elif idx == 4:
            reports = recent_reports()
            if not reports:
                input("No reports saved yet. Press Enter...")
            else:
                labels = [(f.name, "") for f in reports]
                r_idx = menu_choose(labels, "Saved HTML reports")
                if r_idx is not None:
                    open_in_browser(str(reports[r_idx]))

        # 5: Exit
        else:
            print("Bye!")
            return


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if argv and not any(a == "--menu" for a in argv):
        # CLI flags passed (e.g. --date, --html, --user) → use them directly.
        cmd_cli(argv)
    else:
        # No args (or an explicit --menu) → always open the interactive menu.
        run_menu()


if __name__ == "__main__":
    main()
