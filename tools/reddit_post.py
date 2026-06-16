"""
Reddit Post Tool
Posts a text submission to target subreddits from a Markdown draft file.

Usage:
    python tools/reddit_post.py --file drafts/post_11.md --url https://deltantheta.substack.com/p/slug
    python tools/reddit_post.py --file drafts/post_11.md --url <link> --body "Custom summary..."
    python tools/reddit_post.py --file drafts/post_11.md --url <link> --subreddits algotrading investing
    python tools/reddit_post.py --file drafts/post_11.md --url <link> --dry-run

Setup (one-time):
    pip install praw python-dotenv

    1. Go to https://www.reddit.com/prefs/apps
    2. Click "Create another app..." -> type: script
    3. Name: DeltaTheta Publisher, redirect URI: http://localhost:8080
    4. Copy client_id (below app name) and client_secret

Required .env vars:
    REDDIT_CLIENT_ID      -- from reddit.com/prefs/apps (script app)
    REDDIT_CLIENT_SECRET  -- from reddit.com/prefs/apps
    REDDIT_USERNAME       -- Reddit account username
    REDDIT_PASSWORD       -- Reddit account password
    REDDIT_USER_AGENT     -- e.g. "DeltaTheta:v1.0 (by /u/yourname)"

Optional .env vars:
    REDDIT_SUBSTACK_URL   -- base Substack URL for footer (default: https://deltantheta.substack.com)
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(Path(__file__).parent.parent / ".env")

DEFAULT_SUBREDDITS = ["MacroEconomics", "investing", "algotrading"]
REDDIT_SUBSTACK_URL = os.getenv("REDDIT_SUBSTACK_URL", "https://deltantheta.substack.com")

REQUIRED_ENV = [
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USERNAME",
    "REDDIT_PASSWORD",
    "REDDIT_USER_AGENT",
]


def check_credentials() -> dict:
    creds = {k: os.getenv(k) for k in REQUIRED_ENV}
    missing = [k for k, v in creds.items() if not v]
    if missing:
        sys.exit(
            f"ERROR: Missing .env vars: {', '.join(missing)}\n"
            "See tools/reddit_post.py docstring for setup."
        )
    return creds


def extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    sys.exit("ERROR: No H1 title found in draft. Add a '# Title' line.")


def extract_body(text: str) -> str:
    lines = text.splitlines()

    # Drop the H1 title line
    body_lines = []
    skipped_title = False
    for line in lines:
        if not skipped_title and line.startswith("# "):
            skipped_title = True
            continue
        body_lines.append(line)

    # Strip leading blanks, then italic bylines, then blanks again (repeat until stable)
    changed = True
    while changed:
        changed = False
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
            changed = True
        while body_lines and re.match(r"^\*[^*]+\*\s*$", body_lines[0].strip()):
            body_lines.pop(0)
            changed = True

    # Take everything before the first --- separator or ## heading
    intro_lines = []
    for line in body_lines:
        if line.strip() == "---" or line.startswith("## "):
            break
        intro_lines.append(line)

    # Drop trailing blank lines
    while intro_lines and not intro_lines[-1].strip():
        intro_lines.pop()

    body = "\n".join(intro_lines).strip()

    # Strip markdown image syntax: ![alt](path)
    body = re.sub(r"!\[.*?\]\(.*?\)", "", body)

    # Collapse any triple+ blank lines left behind
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    if not body:
        sys.exit(
            "ERROR: Could not extract body from draft — no text found before the first '---' or '##'.\n"
            "Use --body to provide the Reddit summary manually."
        )
    return body


def build_post_body(body: str, url: str) -> str:
    footer = (
        f"\n\n---\n"
        f"Full post + charts: {url}\n\n"
        f"*DeltaTheta — independent macro research. "
        f"[Subscribe]({REDDIT_SUBSTACK_URL})*"
    )
    return body + footer


def submit_post(creds: dict, subreddit: str, title: str, body: str) -> str | None:
    try:
        import praw
    except ImportError:
        sys.exit("ERROR: praw not installed. Run: pip install praw")

    try:
        reddit = praw.Reddit(
            client_id=creds["REDDIT_CLIENT_ID"],
            client_secret=creds["REDDIT_CLIENT_SECRET"],
            username=creds["REDDIT_USERNAME"],
            password=creds["REDDIT_PASSWORD"],
            user_agent=creds["REDDIT_USER_AGENT"],
        )
        submission = reddit.subreddit(subreddit).submit(title=title, selftext=body)
        return f"https://reddit.com{submission.permalink}"
    except Exception as e:
        print(f"  WARN: Failed to post to r/{subreddit}: {e}", file=sys.stderr)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a Markdown draft to Reddit subreddits")
    parser.add_argument("--file", required=True, help="Path to Markdown draft file")
    parser.add_argument("--url", required=True,
                        help="Full Substack post URL (appended to footer)")
    parser.add_argument("--body", default=None,
                        help="Reddit body text (overrides auto-extraction from draft)")
    parser.add_argument("--subreddits", nargs="+", default=DEFAULT_SUBREDDITS,
                        help="Subreddits to post to (default: MacroEconomics investing algotrading)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be posted without posting")
    args = parser.parse_args()

    draft_path = Path(args.file)
    if not draft_path.exists():
        sys.exit(f"ERROR: File not found: {draft_path}")

    text = draft_path.read_text(encoding="utf-8")
    title = extract_title(text)
    body = args.body if args.body else extract_body(text)
    full_body = build_post_body(body, args.url)

    mode = "DRY RUN" if args.dry_run else "POSTING"
    print(f"\n{mode} -> Reddit")
    print(f"  Title      : {title}")
    print(f"  Subreddits : {', '.join(f'r/{s}' for s in args.subreddits)}")
    print(f"  URL        : {args.url}")
    preview = full_body[:500] + ("..." if len(full_body) > 500 else "")
    print(f"\n--- Body preview ---\n{preview}\n---\n")

    if args.dry_run:
        print("Dry run complete — nothing posted.")
        return

    creds = check_credentials()

    for i, subreddit in enumerate(args.subreddits):
        print(f"  Posting to r/{subreddit}...")
        url = submit_post(creds, subreddit, title, full_body)
        if url:
            print(f"  OK  {url}")
        if i < len(args.subreddits) - 1:
            time.sleep(2)

    print("\nDone.")


if __name__ == "__main__":
    main()
