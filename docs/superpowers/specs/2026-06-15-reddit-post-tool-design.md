# Design: Reddit Post Tool

**Date:** 2026-06-15
**Status:** Approved

## Goal

Add `tools/reddit_post.py` to the DnT WAT pipeline. Posts a text submission to r/MacroEconomics, r/investing, and r/algotrading from a Markdown draft file. Follows the same CLI pattern as the existing publishing tools.

## Approach

PRAW (Python Reddit API Wrapper) with script-type OAuth. No browser automation — Reddit's API is clean and PRAW handles auth, rate limits, and submission well.

## CLI

```sh
python tools/reddit_post.py --file drafts/post_11_vol_term_structure.md --url https://deltantheta.substack.com/p/vol-term-structure
python tools/reddit_post.py --file drafts/post_11.md --url <link> --body "Custom summary..."
python tools/reddit_post.py --file drafts/post_11.md --url <link> --subreddits algotrading investing
python tools/reddit_post.py --file drafts/post_11.md --url <link> --dry-run
```

## Post Format

Text submission (not link post). Body = auto-extracted intro paragraphs + Substack link footer.

**Title:** H1 from the draft markdown file.

**Body (auto-extracted):** All text before the first `---` or `##` in the body (after removing the H1 title and the italic byline lines). Strips markdown image syntax. Appended footer:

```text
---
Full post + charts: <SUBSTACK_URL>/p/<slug>

*DeltaTheta — independent macro research. [Subscribe](https://deltantheta.substack.com)*
```

**`--body` override:** When provided, replaces the auto-extracted text entirely (footer still appended).

**`--subreddits` override:** Space-separated list. Default: `MacroEconomics investing algotrading`.

## Credentials (.env)

```text
REDDIT_CLIENT_ID      — from reddit.com/prefs/apps (script app)
REDDIT_CLIENT_SECRET  — from reddit.com/prefs/apps
REDDIT_USERNAME       — Reddit account username
REDDIT_PASSWORD       — Reddit account password
REDDIT_USER_AGENT     — e.g. "DeltaTheta:v1.0 (by /u/yourname)"
REDDIT_SUBSTACK_URL   — https://deltantheta.substack.com (used in footer)
```

## Setup (one-time)

1. Go to reddit.com/prefs/apps → Create app → type: **script**
2. Copy `client_id` (under app name) and `client_secret`
3. Add all five vars to `.env`
4. `pip install praw python-dotenv`

## Behavior

- Posts sequentially to each subreddit with a 2-second pause between posts (Reddit rate limit courtesy)
- Prints submission URL for each successful post
- `--dry-run` prints title + body without posting
- Exits with a clear error message if any `.env` var is missing
- Warns (but does not exit) if a subreddit post fails — continues to remaining subreddits

## Error Handling

| Condition | Behavior |
| --- | --- |
| Missing .env vars | `sys.exit` with list of missing keys |
| Subreddit not found | Warn + skip, continue |
| Reddit API error (rate limit, banned) | Warn + skip, print error message |
| Draft file not found | `sys.exit` |
| No body extractable from draft | `sys.exit` with guidance to use `--body` |

## Files Changed

- `tools/reddit_post.py` — new file
- `.env` — user adds 5 new vars (documented in tool docstring)
- `workflows/reddit_post.md` — new workflow doc

## Out of Scope

- Image uploads (Reddit image+text combos require a separate upload endpoint; Substack link provides the chart)
- Scheduling / delayed posting
- Comment monitoring or reply automation

