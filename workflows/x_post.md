# Workflow: X (Twitter) Post Tool

## Objective

Post a publication-quality chart image with caption to X/Twitter to drive traffic
back to Substack. Charts are the primary content unit — a single chart with a
one-line observation and a Substack link is a complete post.

## One-Time Setup

### 1. Install dependencies

```sh
pip install tweepy python-dotenv
```

### 2. Create an X Developer account and app

1. Go to [developer.twitter.com](https://developer.twitter.com) and sign in with your X account
2. Create a new **Project** and **App** (Free tier is fine — 1,500 posts/month)
3. In App Settings → **User authentication settings**:
   - Enable **OAuth 1.0a**
   - Set permissions to **Read and Write**
   - Set callback URL to `https://localhost` (required field, not actually used)
4. Go to **Keys and Tokens** and generate:
   - API Key and Secret (Consumer Key/Secret)
   - Access Token and Secret (must regenerate after enabling Write permissions)

### 3. Add to .env

```sh
X_API_KEY=...
X_API_SECRET=...
X_ACCESS_TOKEN=...
X_ACCESS_SECRET=...
```

## Execution

**Dry run — preview without posting:**

```sh
python tools/x_post.py --image .tmp/yield_curve_2000_2026.png --caption "The yield curve just re-steepened after the longest inversion on record. Here's 26 years of history and what it tells us about where we are now. [link]" --dry-run
```

**Post to X:**

```sh
python tools/x_post.py --image .tmp/yield_curve_2000_2026.png --caption "The 2s10s re-steepened after the deepest inversion in 40 years. What that means for credit and equity factor exposure. deltantheta.substack.com #fintwit #macro"
```

## Expected Output

```text
POSTING -> x.com
  Image  : .tmp\yield_curve_2000_2026.png
  Caption: The 2s10s re-steepened after the deepest inversion in 40 years...

  Uploading image...
  Posting tweet...

  OK  https://x.com/i/web/status/1234567890
```

## Posting Strategy

**What to post:**
- Every new Substack article → post the primary chart + one-sentence observation + Substack link
- Major data releases (BLS first Friday, FOMC days, COT weekly) → short data point post
  with the relevant chart if available, otherwise text only

**Caption formula:**
```
[one-line observation about what the data shows]
[one-line "why it matters" or implication]
[Substack link]
#fintwit #macro [relevant hashtag e.g. #bonds #employment]
```

**Hashtags that reach the right audience:**
- `#fintwit` — core macro/finance Twitter community
- `#macro` — macro traders
- `#algotrading` — for pipeline/tool posts
- `#bonds` / `#rates` — for yield curve posts
- `#employment` / `#NFP` — for BLS posts (especially on jobs Friday)

**Cadence:**
- 1 post per Substack article (chart post)
- 1–2 data release posts per month
- Do not exceed ~10 posts/week to avoid spammy appearance

## Edge Cases

**"Unauthorized" or 403 error** — Access token was generated before enabling Write
permissions. Go to developer.twitter.com → Keys and Tokens → regenerate Access Token
and Secret, then update `.env`.

**"Media type not supported"** — X requires images to be JPEG or PNG under 5MB.
Charts from `chart_macro.py` are PNG and well under 5MB — this shouldn't occur.

**Caption over 280 chars** — The tool truncates automatically with a warning. Use
`--dry-run` first to check length before posting.

## Security Notes

- X credentials grant full posting access to your account. Keep in `.env` only.
- Never commit credentials — `.env` is gitignored.
