# Workflow: Substack Draft Publisher

## Objective
Convert a Markdown draft in `drafts/` to HTML and create a Substack post
via the internal API. Default mode creates a **draft** for review — you
click Publish yourself.

## One-Time Setup

### 1. Get your session cookie
1. Log into your Substack publication in Chrome or Firefox
2. Open DevTools → F12
3. Navigate to **Application → Cookies → https://substack.com**
4. Find the cookie named `substack.sid`
5. Copy its **Value** (a long string beginning with `s%3A`)

### 2. Add to .env
```
SUBSTACK_PUBLICATION=deltatheta    # subdomain only — no .substack.com
SUBSTACK_SESSION=s%3Axxx...        # full value of substack.sid cookie
```

### 3. Install dependencies (once)
```
pip install markdown requests
```

## Execution

**Create a draft (standard — does NOT publish):**
```
python tools/substack_post.py --file drafts/post_02_wat_framework.md
```

**Publish immediately:**
```
python tools/substack_post.py --file drafts/post_02_wat_framework.md --publish
```

## Expected Output
```
DRAFTING -> deltatheta.substack.com
  Title : WAT — How We're Organizing the Machine
  Source: drafts\post_02_wat_framework.md
  Body  : 8,432 chars HTML

  OK  Post ID : 12345678
      URL     : https://deltatheta.substack.com/p/wat-how-were-organizing-the-machine

  Draft saved. Open Substack to review and publish.
```

## How the Tool Works
1. Reads the draft Markdown file
2. Extracts the first `# H1` as the post title
3. Converts the remaining Markdown to HTML (`fenced_code`, `tables`, `sane_lists`)
4. POSTs to `https://{publication}.substack.com/api/v1/posts` with `draft: true`
5. Returns the Substack post URL

## Edge Cases

**401 Unauthorized** — Session cookie expired. Substack sessions last ~30 days.
Repeat Step 1 above to get a fresh cookie and update `.env`.

**404 Not Found** — `SUBSTACK_PUBLICATION` doesn't match the subdomain.
Check your Substack URL: `https://YOUR-SUBDOMAIN.substack.com`.

**Code blocks look wrong in email** — Substack's email renderer strips some
CSS. The web post renders correctly. For email-heavy posts, keep code blocks
short or link to the GitHub file instead of embedding.

**API shape changes** — This uses Substack's undocumented internal API (as of
June 2026). If it breaks, open DevTools while manually saving a draft in
Substack, watch the Network tab for a POST to `/api/v1/posts`, and update
the payload shape in `create_post()` to match.

## Security Notes
- `SUBSTACK_SESSION` grants full access to your Substack account. Keep it
  in `.env` only — it is gitignored and must never be committed.
- The tool suppresses SSL certificate warnings (same Windows CA issue as
  fred_fetch.py). This is safe for outbound HTTPS calls to Substack.
