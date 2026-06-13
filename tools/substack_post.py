"""
Substack Draft Publisher (Playwright)
Opens a real browser, logs in via session cookie, and creates a Substack
draft from a Markdown file. Browser automation bypasses Cloudflare bot
protection that blocks programmatic API calls.

Usage:
    python tools/substack_post.py --file drafts/post_02_wat_framework.md
    python tools/substack_post.py --file drafts/post_02_wat_framework.md --headless
    python tools/substack_post.py --file drafts/post_02_wat_framework.md --publish

Setup (one-time):
    pip install playwright markdown python-dotenv
    playwright install chromium

Required .env vars:
    SUBSTACK_PUBLICATION  — subdomain only, e.g. "deltantheta"
    SUBSTACK_SESSION      — substack.sid cookie value (see workflows/substack_post.md)
"""

import argparse
import base64
import os
import re
import sys
from pathlib import Path

import markdown
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

PASTE_WAIT_MS  = 2_000   # time to let TipTap process the paste event
AUTOSAVE_WAIT  = 20_000  # ms to wait for Substack's auto-save URL change

TABLE_CSS = """
  body { margin: 0; padding: 12px; background: white; font-family: -apple-system, sans-serif; }
  table { border-collapse: collapse; width: 100%; font-size: 14px; }
  th { background: #1a1a2e; color: white; padding: 10px 14px; text-align: left; font-weight: 600; }
  td { padding: 9px 14px; border-bottom: 1px solid #e5e5e5; color: #1a1a1a; }
  tr:nth-child(even) td { background: #f7f7f7; }
  tr:nth-child(odd) td { background: white; }
"""


def _screenshot_table(table_html: str, context) -> str:
    """Render a single <table> block in a blank browser page and return a base64 <img> tag."""
    page = context.new_page()
    try:
        html_doc = f"<html><head><style>{TABLE_CSS}</style></head><body>{table_html}</body></html>"
        page.set_content(html_doc, wait_until="load")
        table_el = page.locator("table")
        png_bytes = table_el.screenshot()
        b64 = base64.b64encode(png_bytes).decode()
        return f'<img src="data:image/png;base64,{b64}" alt="table">'
    finally:
        page.close()


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


def upload_local_images(page, html: str, base_dir: Path, publication: str) -> str:
    """
    Find <img src="local/path"> tags in html, upload each to Substack via the
    authenticated browser context, and replace src with the returned CDN URL.
    """
    def replace_src(m):
        src = m.group(1)
        if src.startswith("http") or src.startswith("data:"):
            return m.group(0)  # already a URL or inline data URI, leave it
        img_path = (base_dir / src).resolve()
        if not img_path.exists():
            print(f"  WARN: image not found, skipping: {img_path}")
            return m.group(0)
        import base64
        b64 = base64.b64encode(img_path.read_bytes()).decode()
        data_uri = f"data:image/png;base64,{b64}"
        print(f"  Embedded {img_path.name} as data URI ({len(b64)//1024}KB)")
        return m.group(0).replace(src, data_uri)

    return re.sub(r'<img[^>]+src="([^"]+)"', replace_src, html)


def fill_title(page, title: str) -> None:
    """Fill the Substack title textarea."""
    el = page.wait_for_selector('textarea#post-title', timeout=10_000)
    el.click()
    el.fill(title)


def paste_body(page, body_html: str) -> None:
    """Paste HTML into the ProseMirror body editor.

    Uses navigator.clipboard.write() + Ctrl+V so TipTap receives a real paste
    event — synthetic ClipboardEvents are rejected for rich content like tables.
    Falls back to the ClipboardEvent approach if the Clipboard API is unavailable.
    """
    editor = page.locator('[data-testid="editor"].tiptap.ProseMirror')
    if not editor.count():
        sys.exit("ERROR: Could not locate the body editor on the page. The Substack editor layout may have changed.")

    editor.click()

    result = page.evaluate(
        """async (html) => {
            try {
                await navigator.clipboard.write([
                    new ClipboardItem({
                        'text/html': new Blob([html], {type: 'text/html'}),
                        'text/plain': new Blob([' '], {type: 'text/plain'}),
                    })
                ]);
                return 'clipboard-set';
            } catch (e) {
                return 'fallback:' + e.message;
            }
        }""",
        body_html,
    )

    if result == "clipboard-set":
        page.keyboard.press("Control+v")
    else:
        # Clipboard API unavailable — fall back to synthetic ClipboardEvent
        print(f"  WARN: clipboard API not available ({result}), using ClipboardEvent fallback")
        page.evaluate(
            """(html) => {
                const editor = document.querySelector('.tiptap.ProseMirror');
                editor.focus();
                const dt = new DataTransfer();
                dt.setData('text/html', html);
                dt.setData('text/plain', html.replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ').trim());
                editor.dispatchEvent(new ClipboardEvent('paste', {
                    clipboardData: dt, bubbles: true, cancelable: true,
                }));
            }""",
            body_html,
        )


def wait_for_autosave(page, editor_url: str) -> str:
    """Wait for Substack to auto-save and redirect the URL, then return it."""
    try:
        page.wait_for_url(
            lambda url: url != editor_url and "/publish/post/" in url,
            timeout=AUTOSAVE_WAIT,
        )
    except PlaywrightTimeout:
        pass  # auto-save may not change the URL; return whatever we have
    return page.url


def run(publication: str, session: str, title: str, body_html: str, publish: bool, headless: bool, draft_dir: Path = Path(".")) -> str:
    """Drive the browser and return the resulting post URL."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless, slow_mo=100 if not headless else 0)
        context = browser.new_context(
            permissions=["clipboard-read", "clipboard-write"],
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )

        context.add_cookies([{
            "name": "substack.sid",
            "value": session,
            "domain": ".substack.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
        }])

        # Render any markdown tables as screenshots before opening the editor
        if "<table>" in body_html:
            print(f"  Rendering tables as images...")
            body_html = re.sub(
                r"<table>.*?</table>",
                lambda m: _screenshot_table(m.group(0), context),
                body_html,
                flags=re.DOTALL,
            )

        page = context.new_page()

        editor_url = f"https://{publication}.substack.com/publish/post/new"
        print(f"  Opening editor...")
        page.goto(editor_url, wait_until="networkidle", timeout=30_000)

        # Detect redirect to login (expired cookie)
        if "/login" in page.url or "/sign-in" in page.url:
            browser.close()
            sys.exit("ERROR: Redirected to login — session cookie has expired. See workflows/substack_post.md to refresh it.")

        print(f"  Filling title...")
        fill_title(page, title)

        page.wait_for_timeout(500)

        if re.search(r'<img[^>]+src="(?!http)', body_html):
            print(f"  Uploading local images...")
            body_html = upload_local_images(page, body_html, draft_dir, publication)

        print(f"  Pasting body ({len(body_html):,} chars)...")
        paste_body(page, body_html)

        page.wait_for_timeout(PASTE_WAIT_MS)

        # Fire a real keystroke so TipTap marks the document dirty and queues auto-save.
        # (ClipboardEvent alone doesn't trigger TipTap's change detection.)
        page.keyboard.press("End")
        page.wait_for_timeout(300)

        # Click the title to blur the body editor — auto-save fires on blur.
        page.locator("textarea#post-title").click()
        page.wait_for_timeout(500)

        if publish:
            print("  Publishing...")
            try:
                pub_btn = page.wait_for_selector('button:has-text("Publish")', timeout=8_000)
                pub_btn.click()
                # Confirm dialog if it appears
                try:
                    page.wait_for_selector('button:has-text("Confirm")', timeout=5_000).click()
                except PlaywrightTimeout:
                    pass
            except PlaywrightTimeout:
                print("  WARNING: Could not find Publish button. Check the browser window.")
        else:
            print("  Waiting for auto-save...")

        draft_url = wait_for_autosave(page, editor_url)
        browser.close()
        return draft_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a Markdown draft to Substack via browser automation")
    parser.add_argument("--file", required=True, help="Path to Markdown draft file")
    parser.add_argument("--publish", action="store_true", help="Publish immediately (default: save as draft)")
    parser.add_argument("--headless", action="store_true", help="Run browser in background (default: visible window)")
    args = parser.parse_args()

    publication = os.getenv("SUBSTACK_PUBLICATION")
    session = os.getenv("SUBSTACK_SESSION")

    if not publication:
        sys.exit("ERROR: SUBSTACK_PUBLICATION not set in .env")
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

    url = run(publication, session, title, body_html, publish=args.publish, headless=args.headless, draft_dir=draft_path.parent)

    print(f"\n  OK  {url}")
    if not args.publish:
        print("  Draft saved. Open Substack to review and publish.")


if __name__ == "__main__":
    main()
