# Reddit Post Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tools/reddit_post.py` that posts a DeltaTheta draft as a text submission to r/MacroEconomics, r/investing, and r/algotrading via PRAW, plus `workflows/reddit_post.md`.

**Architecture:** PRAW script OAuth — no browser automation. Reads a Markdown draft, extracts the H1 as title and the intro paragraphs (before the first `---` or `##`) as body, appends a Substack footer, then posts sequentially to each target subreddit. Follows the same argparse + `.env` + `--dry-run` pattern as `x_post.py`.

**Tech Stack:** Python 3.11+, `praw`, `python-dotenv`. No new dependencies beyond these two.

---

## File Map

| File | Action | Responsibility |
| --- | --- | --- |
| `tools/reddit_post.py` | Create | CLI entry point, credential check, markdown parsing, PRAW submission, multi-subreddit loop |
| `workflows/reddit_post.md` | Create | Setup instructions, usage examples, expected output, edge cases |

---

### Task 1: Scaffold CLI, credential check, and dry-run skeleton

**Files:**
- Create: `tools/reddit_post.py`

- [ ] **Step 1: Create the file with imports, constants, credential check, and main()**

```python
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
    2. Click "Create another app..." → type: script
    3. Name: DeltaTheta Publisher, redirect URI: http://localhost:8080
    4. Copy client_id (below app name) and client_secret

Required .env vars:
    REDDIT_CLIENT_ID      — from reddit.com/prefs/apps (script app)
    REDDIT_CLIENT_SECRET  — from reddit.com/prefs/apps
    REDDIT_USERNAME       — Reddit account username
    REDDIT_PASSWORD       — Reddit account password
    REDDIT_USER_AGENT     — e.g. "DeltaTheta:v1.0 (by /u/yourname)"

Optional .env vars:
    REDDIT_SUBSTACK_URL   — base Substack URL for footer (default: https://deltantheta.substack.com)
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

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

    creds = check_credentials()

    mode = "DRY RUN" if args.dry_run else "POSTING"
    print(f"\n{mode} -> Reddit")
    print(f"  File       : {draft_path}")
    print(f"  Subreddits : {', '.join(f'r/{s}' for s in args.subreddits)}")
    print(f"  URL        : {args.url}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the skeleton runs**

```sh
python tools/reddit_post.py --file drafts/post_11_vol_term_structure.md --url https://deltantheta.substack.com/p/test --dry-run
```

Expected (credentials must be in `.env` — even placeholder values work at this stage):
```text
DRY RUN -> Reddit
  File       : drafts\post_11_vol_term_structure.md
  Subreddits : r/MacroEconomics, r/investing, r/algotrading
  URL        : https://deltantheta.substack.com/p/test
```

If `.env` vars are missing, the error message lists them by name.

- [ ] **Step 3: Commit**

```sh
git add tools/reddit_post.py
git commit -m "feat: scaffold reddit_post.py with CLI and credential check"
```

---

### Task 2: Markdown parsing — title and body extraction

**Files:**
- Modify: `tools/reddit_post.py`

- [ ] **Step 1: Add `extract_title()` and `extract_body()` functions**

Insert these two functions above `main()`:

```python
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

    # Drop leading italic byline lines like *DeltaTheta | Post N...* and *Written by...*
    while body_lines and re.match(r"^\*[^*]+\*\s*$", body_lines[0].strip()):
        body_lines.pop(0)

    # Drop leading blank lines
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

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
```

- [ ] **Step 2: Wire extraction into `main()` and print a body preview**

Replace the `main()` body after `draft_path.exists()` check with:

```python
    text = draft_path.read_text(encoding="utf-8")
    title = extract_title(text)
    body = args.body if args.body else extract_body(text)

    creds = check_credentials()

    mode = "DRY RUN" if args.dry_run else "POSTING"
    print(f"\n{mode} -> Reddit")
    print(f"  Title      : {title}")
    print(f"  Subreddits : {', '.join(f'r/{s}' for s in args.subreddits)}")
    print(f"  URL        : {args.url}")
    preview = body[:300] + ("..." if len(body) > 300 else "")
    print(f"\n--- Body preview ---\n{preview}\n---\n")
```

- [ ] **Step 3: Verify extraction on the real draft**

```sh
python tools/reddit_post.py --file drafts/post_11_vol_term_structure.md --url https://deltantheta.substack.com/p/test --dry-run
```

Expected: title prints as `The Hidden Buyers and Sellers: Volatility Control Funds and the Realized Vol Term Structure`, body preview shows the opening paragraphs (the hook text before the first `---`), no image markdown visible.

- [ ] **Step 4: Verify `--body` override**

```sh
python tools/reddit_post.py --file drafts/post_11_vol_term_structure.md --url https://deltantheta.substack.com/p/test --body "Custom test body." --dry-run
```

Expected: body preview shows `Custom test body.` instead of the auto-extracted intro.

- [ ] **Step 5: Commit**

```sh
git add tools/reddit_post.py
git commit -m "feat: add markdown title/body extraction to reddit_post.py"
```

---

### Task 3: Footer builder

**Files:**
- Modify: `tools/reddit_post.py`

- [ ] **Step 1: Add `build_post_body()` function**

Insert above `main()`:

```python
def build_post_body(body: str, url: str) -> str:
    footer = (
        f"\n\n---\n"
        f"Full post + charts: {url}\n\n"
        f"*DeltaTheta — independent macro research. "
        f"[Subscribe]({REDDIT_SUBSTACK_URL})*"
    )
    return body + footer
```

- [ ] **Step 2: Wire footer into `main()` and update preview**

After `body = args.body if args.body else extract_body(text)`, add:

```python
    full_body = build_post_body(body, args.url)
```

Update the preview line to use `full_body`:

```python
    preview = full_body[:500] + ("..." if len(full_body) > 500 else "")
    print(f"\n--- Body preview ---\n{preview}\n---\n")
```

- [ ] **Step 3: Verify footer appears in dry-run output**

```sh
python tools/reddit_post.py --file drafts/post_11_vol_term_structure.md --url https://deltantheta.substack.com/p/vol-term-structure --dry-run
```

Expected: preview ends with:
```
---
Full post + charts: https://deltantheta.substack.com/p/vol-term-structure

*DeltaTheta — independent macro research. [Subscribe](https://deltantheta.substack.com)*
```

- [ ] **Step 4: Commit**

```sh
git add tools/reddit_post.py
git commit -m "feat: add Substack footer builder to reddit_post.py"
```

---

### Task 4: PRAW submission and multi-subreddit loop

**Files:**
- Modify: `tools/reddit_post.py`

- [ ] **Step 1: Install PRAW**

```sh
pip install praw
```

- [ ] **Step 2: Add `submit_post()` function**

Insert above `main()`:

```python
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
```

- [ ] **Step 3: Add the posting loop to `main()`**

After the body preview print block, add:

```python
    if args.dry_run:
        print("Dry run complete — nothing posted.")
        return

    for i, subreddit in enumerate(args.subreddits):
        print(f"  Posting to r/{subreddit}...")
        url = submit_post(creds, subreddit, title, full_body)
        if url:
            print(f"  OK  {url}")
        if i < len(args.subreddits) - 1:
            time.sleep(2)

    print("\nDone.")
```

- [ ] **Step 4: Verify end-to-end dry run still works**

```sh
python tools/reddit_post.py --file drafts/post_11_vol_term_structure.md --url https://deltantheta.substack.com/p/vol-term-structure --dry-run
```

Expected: prints full preview, then `Dry run complete — nothing posted.`

- [ ] **Step 5: Add `.env` vars and do a live test to one subreddit**

Add to `.env`:
```text
REDDIT_CLIENT_ID=<your client_id>
REDDIT_CLIENT_SECRET=<your client_secret>
REDDIT_USERNAME=<your username>
REDDIT_PASSWORD=<your password>
REDDIT_USER_AGENT=DeltaTheta:v1.0 (by /u/<your username>)
REDDIT_SUBSTACK_URL=https://deltantheta.substack.com
```

Test against a single low-traffic subreddit first:
```sh
python tools/reddit_post.py --file drafts/post_11_vol_term_structure.md --url https://deltantheta.substack.com/p/vol-term-structure --subreddits test
```

*(Use r/test for a real live submission that won't be seen publicly. Verify the post appears at reddit.com/r/test.)*

- [ ] **Step 6: Commit**

```sh
git add tools/reddit_post.py
git commit -m "feat: add PRAW submission and multi-subreddit posting loop"
```

---

### Task 5: Workflow documentation

**Files:**
- Create: `workflows/reddit_post.md`

- [ ] **Step 1: Create the workflow file**

```markdown
# Workflow: Reddit Post Publisher

## Objective

Post a DeltaTheta draft as a text submission to r/MacroEconomics, r/investing, and r/algotrading
using the Reddit API (PRAW). Always creates a live post — Reddit has no draft mode. Run with
`--dry-run` first to verify the title and body before posting.

## One-Time Setup

### 1. Install dependencies

\```sh
pip install praw python-dotenv
\```

### 2. Create a Reddit app

1. Log in to your Reddit account
2. Go to https://www.reddit.com/prefs/apps
3. Click **"Create another app..."** at the bottom
4. Fill in:
   - **Name:** DeltaTheta Publisher
   - **Type:** script
   - **Redirect URI:** http://localhost:8080
5. Click **Create app**
6. Copy the **client_id** (the string under your app name, below "personal use script")
   and the **client_secret**

### 3. Add to .env

\```sh
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=DeltaTheta:v1.0 (by /u/your_reddit_username)
REDDIT_SUBSTACK_URL=https://deltantheta.substack.com
\```

**Note:** 2FA must be disabled on the Reddit account used for script OAuth.

## Execution

**Dry run first (always):**

\```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure \
    --dry-run
\```

**Post to all three subreddits:**

\```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure
\```

**Post to a single subreddit:**

\```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure \
    --subreddits algotrading
\```

**Custom body (override auto-extraction):**

\```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure \
    --body "Vol-targeting funds mechanically buy and sell based on realized vol..."
\```

## Expected Output

\```text
POSTING -> Reddit
  Title      : The Hidden Buyers and Sellers: Volatility Control Funds and the Realized Vol Term Structure
  Subreddits : r/MacroEconomics, r/investing, r/algotrading
  URL        : https://deltantheta.substack.com/p/vol-term-structure

--- Body preview ---
Most market participants spend their time trying to figure out what earnings will be...
---

  Posting to r/MacroEconomics...
  OK  https://reddit.com/r/MacroEconomics/comments/abc123/the_hidden_buyers_and_sellers/
  Posting to r/investing...
  OK  https://reddit.com/r/investing/comments/def456/the_hidden_buyers_and_sellers/
  Posting to r/algotrading...
  OK  https://reddit.com/r/algotrading/comments/ghi789/the_hidden_buyers_and_sellers/

Done.
\```

## How the Tool Works

1. Reads the draft Markdown file
2. Extracts the H1 as the post title
3. Auto-extracts the intro: all text before the first `---` or `##` heading,
   after stripping the title and italic byline lines
4. Strips markdown image syntax from the extracted body
5. Appends a footer with the full Substack post URL and subscribe link
6. Authenticates with Reddit via PRAW script OAuth
7. Posts a text submission to each target subreddit with a 2-second pause between posts
8. Warns on individual subreddit failures and continues to remaining subreddits

## Edge Cases

**401 / authentication error** — Check `REDDIT_USERNAME` and `REDDIT_PASSWORD` in `.env`.
The account must not have 2FA enabled for script OAuth.

**"you are doing that too much"** — Reddit rate limiter. PRAW handles 429s automatically,
but if it persists wait 10 minutes and retry.

**Subreddit rules rejection** — Some subreddits reject posts from new or low-karma accounts.
Use `--subreddits` to skip problem subreddits and post to the others.

**Body too long** — Reddit text posts have a 40,000 character limit. Auto-extracted intros
are well under this. If using `--body` manually, keep it under 2,000 characters.

**"No body extractable" error** — The draft has no text before its first `---` or `##`.
Use `--body` to provide the summary manually.

## Security Notes

- `REDDIT_PASSWORD` grants full access to your Reddit account. Keep it in `.env` only —
  it is gitignored and must never be committed.
- Use a dedicated Reddit account for bot posting, separate from your personal account.
```

- [ ] **Step 2: Remove the backslashes from the code fence markers**

The backslashes in the file above (`\``) were added to prevent nested fences from breaking this plan document. In the actual `workflows/reddit_post.md` file, write standard triple-backtick fences with no backslashes.

- [ ] **Step 3: Commit**

```sh
git add workflows/reddit_post.md
git commit -m "docs: add reddit_post workflow"
```

---

### Task 6: End-to-end verification

**Files:** none

- [ ] **Step 1: Full dry run on current post**

```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure \
    --dry-run
```

Confirm all of the following in the output:
- Title is the correct H1 from the draft
- Body preview shows the opening hook paragraphs (no `*DeltaTheta | Post 11*` byline, no image markdown)
- Footer shows the correct Substack URL
- `Dry run complete — nothing posted.` printed at end

- [ ] **Step 2: Verify `--subreddits` override**

```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/test \
    --subreddits algotrading \
    --dry-run
```

Expected: `Subreddits : r/algotrading` (only one listed).

- [ ] **Step 3: Verify missing credential error message**

Temporarily rename `.env` or comment out one var, then run:
```sh
python tools/reddit_post.py --file drafts/post_11_vol_term_structure.md --url https://test --dry-run
```

Expected: `ERROR: Missing .env vars: REDDIT_CLIENT_ID` (or whichever is missing).

Restore `.env` after verifying.

- [ ] **Step 4: Final commit if any fixes were needed**

```sh
git add -p
git commit -m "fix: reddit_post.py edge case fixes from verification"
```
