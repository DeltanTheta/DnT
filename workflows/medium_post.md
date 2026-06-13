# Workflow: Medium Cross-Post Publisher

## Objective

Cross-post a Substack draft to Medium for wider audience reach. Medium is used
as a discovery channel — no monetization. The tool automatically appends a
footer linking back to Substack and GitHub so readers can follow the full series.

**Post to Substack first**, then cross-post to Medium. Substack is the primary
publication; Medium drives traffic back to it.

## One-Time Setup

### 1. Install dependencies

```sh
pip install playwright markdown python-dotenv
playwright install chromium
```

Skip if already done for Substack.

### 2. Get your Medium session cookie

1. Log in to **medium.com** in Chrome
2. Open DevTools → F12
3. Navigate to **Application → Cookies → https://medium.com**
4. Find the cookie named `__session`
5. Copy its **Value** (a long string)

### 3. Add to .env

```sh
MEDIUM_SESSION=<value of __session cookie>

# Optional — defaults are already correct for DnT:
# MEDIUM_SUBSTACK_URL=https://deltantheta.substack.com
# MEDIUM_GITHUB_URL=https://github.com/DeltanTheta/DnT
```

## Execution

**Create a draft (default — review before publishing):**

```sh
python tools/medium_post.py --file drafts/post_03_yield_curve.md
```

**Create a draft silently:**

```sh
python tools/medium_post.py --file drafts/post_03_yield_curve.md --headless
```

**Publish immediately:**

```sh
python tools/medium_post.py --file drafts/post_03_yield_curve.md --publish
```

## Expected Output

```text
DRAFTING -> medium.com
  Title : The Yield Curve — What It Measures, Why It Belongs, and the Code to Pull It
  Source: drafts\post_03_yield_curve.md
  Body  : 8,241 chars HTML
  Opening Medium editor...
  Filling title...
  Pasting body (8,872 chars)...
  Draft saved. Visit medium.com/me/stories to review and publish.
  NOTE: Medium allows ~2 published stories/day.

  OK  https://medium.com/new-story
```

After running, go to **medium.com/me/stories** to review the draft and publish.

## What the Tool Adds

The script automatically appends a cross-promotion footer to every Medium post:

> *Originally published on [DeltaTheta Substack](https://deltantheta.substack.com).
> Subscribe there for full charts and future posts.*
>
> *Source code: [github.com/DeltanTheta/DnT](https://github.com/DeltanTheta/DnT)*
>
> ☕ Buy me a coffee

This footer is **not** in the markdown draft — it's injected at post time. The
Substack version of the same post does not get this footer.

## Post Footer Convention (Substack)

Substack post footers should include the GitHub repo link going forward:

```markdown
[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta) · [Source code on GitHub](https://github.com/DeltanTheta/DnT)
```

## Medium Publishing Limits

Medium limits accounts to **approximately 2 published stories per day** to
prevent spam. Plan accordingly — do not batch-publish all back-catalog posts
at once. Draft them in advance and publish on a cadence.

## Edge Cases

**Redirected to login** — `__session` cookie has expired. Repeat step 2 of
setup to get a fresh cookie and update `.env`.

**Title or body field not found** — Medium may have updated their editor
layout. Run without `--headless` to watch the browser, open DevTools, inspect
the title or body element, and update `TITLE_SELECTOR` or `BODY_SELECTOR`
at the top of `tools/medium_post.py`. This is the same process used to fix
the Substack selectors (see git history: commit 657f359).

**Images missing on Medium** — Medium may strip base64 data URIs from pasted
content. The text will be intact. For image-heavy posts, consider adding a
note: *"Charts available in the [full post on Substack](...)"*.

**Publish button not found** — Medium's publish flow has multiple steps and
dialog variants. If the script can't find the button, run without `--headless`
and complete the publish step manually after the script pastes the content.

## Security Notes

- `MEDIUM_SESSION` grants full access to your Medium account. Keep it in
  `.env` only — gitignored and never committed.
- The browser automation runs entirely locally.
