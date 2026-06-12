"""
Substack Draft Publisher
Converts a Markdown draft to HTML and creates a post via Substack's
unofficial internal API. Posts as DRAFT by default — review and click
Publish yourself in the Substack editor.

Usage:
    python tools/substack_post.py --file drafts/post_02_wat_framework.md
    python tools/substack_post.py --file drafts/post_02_wat_framework.md --publish

Required .env vars:
    SUBSTACK_PUBLICATION  — publication subdomain (e.g. "deltatheta")
    SUBSTACK_SESSION      — substack.sid cookie value (see workflows/substack_post.md)
"""

import argparse
import os
import sys
import warnings
from pathlib import Path

import markdown
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv(Path(__file__).parent.parent / ".env")


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists"],
    )


def extract_title(text: str) -> tuple[str, str]:
    """Pull the first H1 as the post title; return (title, remaining_body)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body = "\n".join(lines[:i] + lines[i + 1:]).strip()
            return title, body
    return "Untitled", text


def create_post(publication: str, session: str, title: str, body_html: str, publish: bool) -> dict:
    url = f"https://{publication}.substack.com/api/v1/posts"
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"substack.sid={session}",
        "User-Agent": "Mozilla/5.0",
    }
    payload = {
        "title": title,
        "draft_title": title,
        "draft_subtitle": "",
        "draft_body": body_html,
        "type": "newsletter",
        "draft": not publish,
        "audience": "everyone",
    }
    resp = requests.post(url, headers=headers, json=payload, verify=False)
    if resp.status_code == 401:
        sys.exit("ERROR: 401 Unauthorized — session cookie has expired. See workflows/substack_post.md to refresh it.")
    if resp.status_code == 404:
        sys.exit(f"ERROR: 404 — check that SUBSTACK_PUBLICATION='{publication}' matches your subdomain exactly.")
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a Markdown draft to Substack")
    parser.add_argument("--file", required=True, help="Path to Markdown draft file")
    parser.add_argument("--publish", action="store_true", help="Publish immediately (default: save as draft)")
    args = parser.parse_args()

    publication = os.getenv("SUBSTACK_PUBLICATION")
    session = os.getenv("SUBSTACK_SESSION")

    if not publication:
        sys.exit("ERROR: SUBSTACK_PUBLICATION not set in .env (e.g. deltatheta)")
    if not session:
        sys.exit("ERROR: SUBSTACK_SESSION not set in .env — see workflows/substack_post.md")

    draft_path = Path(args.file)
    if not draft_path.exists():
        sys.exit(f"ERROR: File not found: {draft_path}")

    text = draft_path.read_text(encoding="utf-8")
    title, body = extract_title(text)
    body_html = md_to_html(body)

    mode = "PUBLISHING" if args.publish else "DRAFTING"
    print(f"\n{mode} -> {publication}.substack.com")
    print(f"  Title : {title}")
    print(f"  Source: {draft_path}")
    print(f"  Body  : {len(body_html):,} chars HTML")

    result = create_post(publication, session, title, body_html, publish=args.publish)

    post_id = result.get("id", "unknown")
    slug = result.get("slug", str(post_id))
    post_url = result.get("canonical_url") or f"https://{publication}.substack.com/p/{slug}"

    print(f"\n  OK  Post ID : {post_id}")
    print(f"      URL     : {post_url}")
    if not args.publish:
        print("\n  Draft saved. Open Substack to review and publish.")


if __name__ == "__main__":
    main()
