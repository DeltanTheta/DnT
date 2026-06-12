# Workflow: Substack Draft Publisher

## Objective

Convert a Markdown draft in `drafts/` to HTML and create a Substack post
via browser automation. Default mode creates a **draft** for review — you
click Publish yourself.

## One-Time Setup

### 1. Install dependencies

```sh
pip install playwright markdown python-dotenv
playwright install chromium
```

The `playwright install chromium` step downloads a ~150MB browser — once only.

### 2. Get your session cookie

1. Log into your Substack publication in Chrome or Firefox
2. Open DevTools → F12
3. Navigate to **Application → Cookies → <https://substack.com>**
4. Find the cookie named `substack.sid`
5. Copy its **Value** (a long string beginning with `s%3A`)

### 3. Add to .env

```sh
SUBSTACK_PUBLICATION=deltantheta   # subdomain only — no .substack.com
SUBSTACK_SESSION=s%3Axxx...        # full value of substack.sid cookie
```

## Execution

**Create a draft — browser window visible (default):**

```sh
python tools/substack_post.py --file drafts/post_02_wat_framework.md
```

**Create a draft — browser runs silently in background:**

```sh
python tools/substack_post.py --file drafts/post_02_wat_framework.md --headless
```

**Publish immediately:**

```sh
python tools/substack_post.py --file drafts/post_02_wat_framework.md --publish
```

## Expected Output

```text
DRAFTING -> deltantheta.substack.com
  Title : WAT — How We're Organizing the Machine
  Source: drafts\post_02_wat_framework.md
  Body  : 9,992 chars HTML
  Opening editor...
  Filling title...
  Pasting body (9,992 chars)...
  Waiting for auto-save...

  OK  https://deltantheta.substack.com/publish/post/12345678
  Draft saved. Open Substack to review and publish.
```

## How the Tool Works

1. Reads the draft Markdown file
2. Extracts the first `# H1` as the post title
3. Converts the remaining Markdown to HTML (`fenced_code`, `tables`, `sane_lists`)
4. Launches a Chromium browser with the session cookie injected
5. Navigates to `{publication}.substack.com/publish/post/new`
6. Types the title and pastes the HTML body via a `ClipboardEvent`
7. Waits for Substack's auto-save, then returns the draft URL

Using a real browser (rather than direct API calls) bypasses Cloudflare's
bot management, which blocks programmatic POST requests.

## Edge Cases

**Redirected to login** — Session cookie has expired (~30 days). Repeat
Step 2 above to get a fresh cookie and update `.env`.

**Editor not found** — Substack may have changed their editor layout.
Run without `--headless` to watch what's happening in the browser window,
then update the selectors in `fill_title()` or `paste_body()` in the tool.

**Body content missing or garbled** — The `ClipboardEvent` paste approach
works with Substack's ProseMirror editor but may need adjustment if Substack
updates their editor. Check the browser window (run without `--headless`)
to see what got pasted.

**Code blocks look wrong in email** — Substack's email renderer strips some
CSS. The web post renders correctly. For email-heavy posts, link to GitHub
instead of embedding long code blocks.

## Security Notes

- `SUBSTACK_SESSION` grants full access to your Substack account. Keep it
  in `.env` only — it is gitignored and must never be committed.
- The browser automation runs entirely locally; no credentials leave your machine.
