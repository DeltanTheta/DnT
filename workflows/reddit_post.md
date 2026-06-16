# Workflow: Reddit Post Publisher

## Objective

Post a DeltaTheta draft as a text submission to r/MacroEconomics, r/investing, and r/algotrading
using the Reddit API (PRAW). Always creates a live post — Reddit has no draft mode. Run with
`--dry-run` first to verify the title and body before posting.

## One-Time Setup

### 1. Install dependencies

```sh
pip install praw python-dotenv
```

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

```sh
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
REDDIT_USER_AGENT=DeltaTheta:v1.0 (by /u/your_reddit_username)
REDDIT_SUBSTACK_URL=https://deltantheta.substack.com
```

**Note:** 2FA must be disabled on the Reddit account used for script OAuth.

## Execution

**Dry run first (always):**

```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure \
    --dry-run
```

**Post to all three subreddits:**

```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure
```

**Post to a single subreddit:**

```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure \
    --subreddits algotrading
```

**Custom body (override auto-extraction):**

```sh
python tools/reddit_post.py \
    --file drafts/post_11_vol_term_structure.md \
    --url https://deltantheta.substack.com/p/vol-term-structure \
    --body "Vol-targeting funds mechanically buy and sell based on realized vol..."
```

## Expected Output

```text
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
```

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
