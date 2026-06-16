"""
X (Twitter) Post Tool
Posts a chart image with caption text to X/Twitter using the API v2.

Usage:
    python tools/x_post.py --image .tmp/yield_curve_2000_2026.png --caption "caption text"
    python tools/x_post.py --image .tmp/yield_curve.png --caption "..." --dry-run

Setup (one-time):
    pip install tweepy python-dotenv

    Get API credentials at developer.twitter.com:
    1. Create a project and app (Free tier is sufficient — 1,500 posts/month)
    2. Enable OAuth 1.0a with Read and Write permissions
    3. Generate Access Token and Secret
    4. Copy all five values to .env (see Required .env vars below)

Required .env vars:
    X_API_KEY         — API Key (Consumer Key)
    X_API_SECRET      — API Key Secret (Consumer Secret)
    X_ACCESS_TOKEN    — Access Token
    X_ACCESS_SECRET   — Access Token Secret

Notes:
    - Images are uploaded via v1.1 media upload (still required for media attachments)
    - Tweet text is posted via API v2
    - Free tier: 1,500 tweets/month — well above expected posting cadence
    - --dry-run prints what would be posted without hitting the API
"""

import argparse
import os
import re
import ssl
import sys
from pathlib import Path

import urllib3
from dotenv import load_dotenv

# Python 3.14 on Windows ships without bundled CA certs; patch both ssl and
# requests/urllib3 (tweepy uses requests, which bypasses ssl._create_default_https_context)
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests  # noqa: E402 — must import after urllib3 patch
_orig_send = requests.Session.send
def _send_no_verify(self, *args, **kwargs):
    kwargs["verify"] = False
    return _orig_send(self, *args, **kwargs)
requests.Session.send = _send_no_verify

load_dotenv(Path(__file__).parent.parent / ".env")


def post(image_path: Path, caption: str, dry_run: bool = False) -> str:
    """Upload image and post tweet. Returns the tweet URL."""
    try:
        import tweepy
    except ImportError:
        sys.exit("ERROR: tweepy not installed. Run: pip install tweepy")

    api_key = os.getenv("X_API_KEY")
    api_secret = os.getenv("X_API_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_secret = os.getenv("X_ACCESS_SECRET")

    missing = [k for k, v in {
        "X_API_KEY": api_key,
        "X_API_SECRET": api_secret,
        "X_ACCESS_TOKEN": access_token,
        "X_ACCESS_SECRET": access_secret,
    }.items() if not v]

    if missing:
        sys.exit(f"ERROR: Missing .env vars: {', '.join(missing)}\nSee tools/x_post.py docstring for setup.")

    if dry_run:
        print(f"\n[DRY RUN] Would post to X:")
        print(f"  Image  : {image_path}")
        print(f"  Caption: {caption}")
        print(f"  Length : {len(caption)} chars (limit: 280)")
        if len(caption) > 280:
            print(f"  WARNING: Caption exceeds 280 characters — will be truncated by X")
        return "dry-run"

    if not image_path.exists():
        sys.exit(f"ERROR: Image not found: {image_path}")

    # Twitter counts every URL as 23 chars (t.co shortening) regardless of actual length
    url_pattern = re.compile(r'https?://\S+')
    def twitter_len(text):
        collapsed = url_pattern.sub('_' * 23, text)
        return len(collapsed)

    actual_len = twitter_len(caption)
    if actual_len > 280:
        print(f"  WARN: Caption is {actual_len} Twitter-chars — X limit is 280. Truncating.")
        # Trim non-URL text to fit
        urls = url_pattern.findall(caption)
        url_chars = sum(23 for _ in urls)
        text_budget = 277 - url_chars
        no_url = url_pattern.sub('', caption).strip()
        caption = no_url[:text_budget] + "... " + " ".join(urls)

    # v1.1 client for media upload (still required)
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api_v1 = tweepy.API(auth)

    print(f"  Uploading image...")
    media = api_v1.media_upload(filename=str(image_path))
    media_id = media.media_id_string

    # v2 client for posting
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret,
    )

    print(f"  Posting tweet...")
    response = client.create_tweet(text=caption, media_ids=[media_id])
    tweet_id = response.data["id"]
    return f"https://x.com/i/web/status/{tweet_id}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Post a chart image to X/Twitter")
    parser.add_argument("--image", required=True, help="Path to image file (.png, .jpg)")
    parser.add_argument("--caption", required=True, help="Tweet text (max 280 chars)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be posted without posting")
    args = parser.parse_args()

    image_path = Path(args.image)

    mode = "DRY RUN" if args.dry_run else "POSTING"
    print(f"\n{mode} -> x.com")
    print(f"  Image  : {image_path}")
    print(f"  Caption: {args.caption[:80]}{'...' if len(args.caption) > 80 else ''}")

    url = post(image_path, args.caption, dry_run=args.dry_run)

    if url != "dry-run":
        print(f"\n  OK  {url}")


if __name__ == "__main__":
    main()
