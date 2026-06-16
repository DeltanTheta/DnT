"""
Medium Story Publisher (Playwright)
Opens a real browser, logs in via session cookie, and creates a Medium
story from a Markdown file. Automatically appends a cross-promotion footer
linking back to Substack and GitHub.

Usage:
    python tools/medium_post.py --file drafts/post_03_yield_curve.md
    python tools/medium_post.py --file drafts/post_03_yield_curve.md --headless
    python tools/medium_post.py --file drafts/post_03_yield_curve.md --publish

Setup (one-time):
    pip install playwright markdown python-dotenv
    playwright install chromium

Required .env vars:
    MEDIUM_SESSION      — __session cookie from medium.com (see workflow)

Optional .env vars (have sensible defaults):
    MEDIUM_SUBSTACK_URL — your Substack URL (default: https://deltantheta.substack.com)
    MEDIUM_GITHUB_URL   — your GitHub repo URL (default: https://github.com/DeltanTheta/DnT)

Optional .env vars (images):
    GITHUB_TOKEN        — Personal Access Token with repo scope (github.com → Settings →
                          Developer settings → Personal access tokens → Fine-grained or Classic).
                          When set, local images are uploaded to assets/ via the GitHub API and
                          referenced by raw.githubusercontent.com URL, which Medium renders correctly.
    - Medium enforces ~2 published stories per day
    - BMC embeds are not supported on Medium; a plain link is used instead
    - AI-assisted disclosure: set manually on Medium after drafting if desired

Getting your __session cookie (one-time):
    1. Log in to medium.com in Chrome
    2. DevTools (F12) → Application → Cookies → https://medium.com
    3. Copy the value of the cookie named __session
    4. Set MEDIUM_SESSION=<value> in .env
    Cookies are long-lived but refresh if you get redirect-to-login errors.
"""

import argparse
import base64
import os
import re
import ssl
import sys
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import HTTPError

import json
import markdown
from dotenv import load_dotenv
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv(Path(__file__).parent.parent / ".env")

PASTE_WAIT_MS = 5_000
AUTOSAVE_WAIT_MS = 4_000

MEDIUM_SUBSTACK_URL = os.getenv("MEDIUM_SUBSTACK_URL", "https://deltantheta.substack.com")
MEDIUM_GITHUB_URL = os.getenv("MEDIUM_GITHUB_URL", "https://github.com/DeltanTheta/DnT")

_gh_parts = MEDIUM_GITHUB_URL.rstrip("/").split("/")
GITHUB_REPO = "/".join(_gh_parts[-2:])   # e.g. "DeltanTheta/DnT"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Medium editor selectors — update via DOM inspection if these fail (see workflow edge cases)
TITLE_SELECTOR = 'h1[data-testid="title"], h1[contenteditable="true"], div[data-testid="editorTitle"] h1'
BODY_SELECTOR = 'div[contenteditable="true"][data-testid="editorParagraph"], div.ProseMirror, section[contenteditable="true"]'


def _cross_post_footer(substack_url: str, github_url: str) -> str:
    return f"""

---

*Originally published on [DeltaTheta Substack]({substack_url}). Subscribe there for full charts and future posts.*

*Source code: [github.com/DeltanTheta/DnT]({github_url})*

[☕ Buy me a coffee](https://buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
"""


def md_to_html(text: str) -> str:
    html = markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists"],
    )
    # Medium's paste handler truncates at <hr> — replace with a blank paragraph
    html = html.replace("<hr />", "<p></p>").replace("<hr>", "<p></p>")
    return html


def extract_title(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("# "):
            title = line[2:].strip()
            body = "\n".join(lines[:i] + lines[i + 1:]).strip()
            return title, body
    return "Untitled", text


def upload_image_via_api(img_path: Path, token: str) -> str | None:
    """Upload a single image to GitHub repo via Contents API. Returns raw URL or None."""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/assets/{img_path.name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }

    # Check if file already exists (need its SHA to update)
    sha = None
    try:
        req = urllib_request.Request(api_url, headers=headers)
        with urllib_request.urlopen(req) as resp:
            sha = json.loads(resp.read())["sha"]
    except HTTPError as e:
        if e.code != 404:
            print(f"  WARN: GitHub API check failed for {img_path.name}: {e}", file=sys.stderr)
            return None

    payload = {
        "message": f"assets: add {img_path.name} for Medium post",
        "content": base64.b64encode(img_path.read_bytes()).decode(),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    try:
        data = json.dumps(payload).encode()
        req = urllib_request.Request(api_url, data=data, headers=headers, method="PUT")
        with urllib_request.urlopen(req) as resp:
            resp.read()
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/assets/{img_path.name}"
        print(f"  Uploaded {img_path.name} -> {raw_url}")
        return raw_url
    except Exception as e:
        print(f"  WARN: GitHub API upload failed for {img_path.name}: {e}", file=sys.stderr)
        return None


def publish_images_to_github(local_paths: list[Path]) -> dict[Path, str]:
    """Upload images to GitHub via API. Returns {local_path: raw_githubusercontent URL}."""
    import time

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("  WARN: GITHUB_TOKEN not set — images will not display on Medium", file=sys.stderr)
        return {}

    path_to_url = {}
    for img_path in local_paths:
        url = upload_image_via_api(img_path, token)
        if url:
            path_to_url[img_path] = url

    return path_to_url


def embed_local_images(html: str, base_dir: Path) -> str:
    # First pass: collect all distinct local image paths
    src_to_path: dict[str, Path] = {}
    for m in re.finditer(r'<img[^>]+src="([^"]+)"', html):
        src = m.group(1)
        if src.startswith("http") or src.startswith("data:"):
            continue
        img_path = (base_dir / src).resolve()
        if not img_path.exists():
            print(f"  WARN: image not found, skipping: {img_path}")
            continue
        src_to_path[src] = img_path

    if not src_to_path:
        return html

    # Upload images to GitHub assets/ for storage
    publish_images_to_github(list(src_to_path.values()))

    # Replace img tags with visible placeholders — Medium's automated proxy is
    # unreliable for external URLs. User inserts images manually via the editor.
    print("\n  Images must be inserted manually in Medium:")
    for img_path in src_to_path.values():
        print(f"    -> Look for [INSERT IMAGE: {img_path.name}] in the draft")
        print(f"       File: assets/{img_path.name}  (or drag from .tmp/)")

    def replace_img(m):
        src = m.group(1)
        img_path = src_to_path.get(src)
        if img_path is None:
            return m.group(0)
        return f'<p>[INSERT IMAGE: {img_path.name}]</p>'

    return re.sub(r'<img[^>]+src="([^"]+)"[^>]*/?>', replace_img, html)


def paste_html(page, html: str) -> None:
    result = page.evaluate(
        """async (html) => {
            try {
                await navigator.clipboard.write([
                    new ClipboardItem({
                        'text/html': new Blob([html], {type: 'text/html'}),
                        'text/plain': new Blob([' '], {type: 'text/plain'}),
                    })
                ]);
                return 'ok';
            } catch (e) {
                return 'err:' + e.message;
            }
        }""",
        html,
    )
    if result == "ok":
        page.keyboard.press("Control+v")
    else:
        print(f"  WARN: clipboard API failed ({result}), trying ClipboardEvent fallback")
        page.evaluate(
            """(html) => {
                const el = document.activeElement;
                const dt = new DataTransfer();
                dt.setData('text/html', html);
                dt.setData('text/plain', ' ');
                el.dispatchEvent(new ClipboardEvent('paste', {
                    clipboardData: dt, bubbles: true, cancelable: true,
                }));
            }""",
            html,
        )


STORAGE_STATE = Path(__file__).parent.parent / ".tmp" / "medium_auth.json"


def login() -> None:
    """Open a browser, let the user log in manually, then save storage state."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            channel="msedge",
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto("https://medium.com/m/signin", wait_until="networkidle", timeout=30_000)
        print("\nLog in to Medium in the browser window, then press Enter here...")
        input()
        STORAGE_STATE.parent.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(STORAGE_STATE))
        browser.close()
        print(f"  Auth saved to {STORAGE_STATE}")


def run(title: str, body_html: str, publish: bool, headless: bool,
        draft_dir: Path = Path(".")) -> str:
    if not STORAGE_STATE.exists():
        sys.exit(
            "ERROR: No saved login found.\n"
            "  Run once with --login to authenticate:\n"
            "  python tools/medium_post.py --login"
        )

    footer_html = md_to_html(_cross_post_footer(MEDIUM_SUBSTACK_URL, MEDIUM_GITHUB_URL))
    full_html = body_html + footer_html

    if re.search(r'<img[^>]+src="(?!http|data:)', full_html):
        print("  Embedding local images...")
        full_html = embed_local_images(full_html, draft_dir)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            channel="msedge",
            args=["--disable-blink-features=AutomationControlled"],
            slow_mo=100 if not headless else 0,
        )
        context = browser.new_context(
            storage_state=str(STORAGE_STATE),
            permissions=["clipboard-read", "clipboard-write"],
            viewport={"width": 1280, "height": 900},
        )

        page = context.new_page()

        print("  Opening Medium editor...")
        page.goto("https://medium.com/new-story", wait_until="networkidle", timeout=30_000)

        if any(x in page.url for x in ["/m/signin", "/login", "accounts.google"]):
            browser.close()
            sys.exit(
                "ERROR: Redirected to login — saved session has expired.\n"
                "  Re-authenticate with: python tools/medium_post.py --login"
            )

        # Fill title — try CSS selector first, then JS fallback
        title_el = None
        try:
            title_el = page.wait_for_selector(TITLE_SELECTOR, timeout=8_000)
        except PlaywrightTimeout:
            pass

        if title_el is None:
            # JS fallback: find the first contenteditable with Title-like placeholder
            handle = page.evaluate_handle("""() => {
                const candidates = [...document.querySelectorAll('[contenteditable="true"], [contenteditable="plaintext-only"]')];
                return candidates.find(el => {
                    const ph = (el.getAttribute('data-placeholder') || el.getAttribute('placeholder') || '').toLowerCase();
                    const tag = el.tagName.toLowerCase();
                    return ph.includes('title') || tag === 'h1';
                }) || candidates[0] || null;
            }""")
            if handle:
                title_el = handle.as_element()

        if title_el is None:
            browser.close()
            sys.exit(
                "ERROR: Could not find title field. Medium's editor may have changed.\n"
                "  Run without --headless, open DevTools, inspect the title element,\n"
                "  and update TITLE_SELECTOR in tools/medium_post.py."
            )

        print("  Filling title...")
        title_el.click()
        page.keyboard.type(title, delay=30)
        page.wait_for_timeout(300)

        # Focus body editor and paste — CSS selector first, then JS fallback
        body_el = None
        try:
            loc = page.locator(BODY_SELECTOR).first
            loc.click(timeout=5_000)
            body_el = loc
        except Exception:
            pass

        if body_el is None:
            handle = page.evaluate_handle("""() => {
                const all = [...document.querySelectorAll('[contenteditable="true"], [contenteditable="plaintext-only"]')];
                // skip the title (first h1), return the next editable
                return all.find(el => el.tagName.toLowerCase() !== 'h1') || all[1] || null;
            }""")
            if handle:
                body_el = handle.as_element()
                try:
                    body_el.click()
                except Exception:
                    body_el = None

        if body_el is None:
            browser.close()
            sys.exit(
                "ERROR: Could not find body editor. Medium's editor may have changed.\n"
                "  Inspect the editor element and update BODY_SELECTOR in tools/medium_post.py."
            )

        # Scale paste wait with content size — large posts need more render time
        paste_wait = max(PASTE_WAIT_MS, min(20_000, len(full_html) // 2))
        print(f"  Pasting body ({len(full_html):,} chars), waiting {paste_wait // 1000}s...")
        paste_html(page, full_html)
        page.wait_for_timeout(paste_wait)

        # Trigger autosave
        page.keyboard.press("End")
        page.wait_for_timeout(AUTOSAVE_WAIT_MS)

        if publish:
            print("  Publishing...")
            try:
                pub_btn = page.wait_for_selector(
                    'button:has-text("Publish"), button:has-text("Publish story")',
                    timeout=8_000,
                )
                pub_btn.click()
                page.wait_for_timeout(2_000)
                # Confirm dialog variants
                for confirm_text in ["Publish now", "Publish story", "Confirm"]:
                    try:
                        page.wait_for_selector(f'button:has-text("{confirm_text}")', timeout=3_000).click()
                        break
                    except PlaywrightTimeout:
                        continue
            except PlaywrightTimeout:
                print("  WARNING: Could not find Publish button. Check browser window.")
        else:
            print("  Draft saved. Visit medium.com/me/stories to review and publish.")
            print("  NOTE: Medium allows ~2 published stories/day.")

        url = page.url
        browser.close()
        return url


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a Markdown draft to Medium via browser automation")
    parser.add_argument("--login", action="store_true", help="Authenticate interactively and save session (run once)")
    parser.add_argument("--file", help="Path to Markdown draft file")
    parser.add_argument("--publish", action="store_true", help="Publish immediately (default: save as draft)")
    parser.add_argument("--headless", action="store_true", help="Run browser in background (default: visible)")
    args = parser.parse_args()

    if args.login:
        login()
        return

    if not args.file:
        sys.exit("ERROR: --file is required (or use --login to authenticate first)")

    draft_path = Path(args.file)
    if not draft_path.exists():
        sys.exit(f"ERROR: File not found: {draft_path}")

    text = draft_path.read_text(encoding="utf-8")
    title, body = extract_title(text)
    body_html = md_to_html(body)

    mode = "PUBLISHING" if args.publish else "DRAFTING"
    print(f"\n{mode} -> medium.com")
    print(f"  Title : {title}")
    print(f"  Source: {draft_path}")
    print(f"  Body  : {len(body_html):,} chars HTML")

    url = run(title, body_html, publish=args.publish, headless=args.headless,
              draft_dir=draft_path.parent)

    print(f"\n  OK  {url}")


if __name__ == "__main__":
    main()
