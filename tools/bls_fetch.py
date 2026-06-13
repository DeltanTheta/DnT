"""
BLS Employment Data Fetcher
Downloads labor market time-series from the Bureau of Labor Statistics public API v2.
No API key required for basic use; set BLS_API_KEY in .env for extended history.

Without key: up to 10 series/request, 10-year windows (auto-chunked)
With key:    up to 50 series/request, 20-year windows

Usage:
    # Default employment dashboard (unemployment, payrolls, earnings, participation)
    python tools/bls_fetch.py --out .tmp/bls_employment.csv

    # Specific series
    python tools/bls_fetch.py --series LNS14000000 CES0000000001 --start 2010 --end 2024

    # NFP sector breakdown
    python tools/bls_fetch.py --preset sectors --out .tmp/bls_sectors.csv

    # List all preset series
    python tools/bls_fetch.py --list-series
"""

import argparse
import json
import ssl
import sys
import time
import warnings
from pathlib import Path

import pandas as pd
import requests
import urllib3
from dotenv import load_dotenv
import os

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv(Path(__file__).parent.parent / ".env")

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Preset series groups
PRESETS = {
    "dashboard": {
        "LNS14000000":  "Unemployment Rate (U-3, SA)",
        "LNS13327709":  "U-6 Unemployment (Broad, SA)",
        "LNS11300000":  "Labor Force Participation Rate (SA)",
        "CES0000000001": "Total Nonfarm Payrolls (thousands, SA)",
        "CES0500000003": "Avg Hourly Earnings, All Private (SA)",
        "CES0500000002": "Avg Weekly Hours, All Private (SA)",
    },
    "sectors": {
        "CES0000000001": "Total Nonfarm",
        "CES2000000001": "Construction",
        "CES3000000001": "Manufacturing",
        "CES4142000001": "Trade, Transport & Utilities",
        "CES5500000001": "Financial Activities",
        "CES6000000001": "Professional & Business Services",
        "CES6500000001": "Education & Health Services",
        "CES7000000001": "Leisure & Hospitality",
        "CES9091000001": "Federal Government",
        "CES9092000001": "State Government",
    },
    "wages": {
        "CES0500000003": "Avg Hourly Earnings, All Private",
        "CES0500000008": "Avg Hourly Earnings, Goods-Producing",
        "CES0800000003": "Avg Hourly Earnings, Private Service",
        "CES0500000002": "Avg Weekly Hours, All Private",
        "CES0500000011": "Avg Weekly Hours, Overtime (Manufacturing)",
    },
}

# Flat lookup of all known series
ALL_KNOWN = {sid: label for group in PRESETS.values() for sid, label in group.items()}


def fetch_bls(series_ids: list[str], start_year: int, end_year: int, api_key: str | None) -> dict:
    """POST to BLS API v2 and return the raw JSON response."""
    payload: dict = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    if api_key:
        payload["registrationkey"] = api_key

    headers = {"Content-type": "application/json"}
    r = requests.post(BLS_API_URL, data=json.dumps(payload), headers=headers, timeout=30, verify=False)
    r.raise_for_status()
    return r.json()


def parse_response(response: dict) -> pd.DataFrame:
    """Convert BLS JSON response to a tidy DataFrame indexed by date."""
    if response.get("status") != "REQUEST_SUCCEEDED":
        msgs = response.get("message", [])
        sys.exit(f"BLS API error: {msgs}")

    series_frames = []
    for s in response["Results"]["series"]:
        sid = s["seriesID"]
        rows = []
        for obs in s["data"]:
            period = obs["period"]
            if not period.startswith("M"):
                continue  # skip annual/quarterly entries
            month = int(period[1:])
            year = int(obs["year"])
            try:
                val = float(obs["value"])
            except (ValueError, KeyError):
                val = float("nan")
            rows.append({"date": pd.Timestamp(year=year, month=month, day=1), sid: val})
        if rows:
            series_frames.append(pd.DataFrame(rows).set_index("date"))

    if not series_frames:
        return pd.DataFrame()

    df = series_frames[0]
    for frame in series_frames[1:]:
        df = df.join(frame, how="outer")
    return df.sort_index()


def fetch_range(series_ids: list[str], start_year: int, end_year: int,
                api_key: str | None, chunk_size: int) -> pd.DataFrame:
    """Fetch over multiple year chunks and concatenate."""
    frames = []
    year = start_year
    while year <= end_year:
        chunk_end = min(year + chunk_size - 1, end_year)
        print(f"  Fetching {len(series_ids)} series: {year}–{chunk_end} ...", end=" ")
        try:
            resp = fetch_bls(series_ids, year, chunk_end, api_key)
            chunk_df = parse_response(resp)
            print(f"{len(chunk_df)} rows")
            frames.append(chunk_df)
        except Exception as e:
            print(f"WARN: {e}")
        year = chunk_end + 1
        if year <= end_year:
            time.sleep(0.5)  # be polite

    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames)
    return df[~df.index.duplicated(keep="last")].sort_index()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch BLS employment data")
    parser.add_argument("--series", nargs="+", help="One or more BLS series IDs")
    parser.add_argument("--preset", choices=list(PRESETS.keys()),
                        default="dashboard", help="Named series group (default: dashboard)")
    parser.add_argument("--start", type=int, default=2000, help="Start year (default: 2000)")
    parser.add_argument("--end", type=int, default=2025, help="End year (default: 2025)")
    parser.add_argument("--out", default=None, help="Output CSV path")
    parser.add_argument("--list-series", action="store_true", dest="list_series",
                        help="Print all known series IDs and exit")
    args = parser.parse_args()

    if args.list_series:
        for preset_name, series_map in PRESETS.items():
            print(f"\n[{preset_name}]")
            for sid, label in series_map.items():
                print(f"  {sid}  {label}")
        return

    raw_key = os.getenv("BLS_API_KEY") or ""
    api_key = raw_key if (raw_key and "your_" not in raw_key.lower() and len(raw_key) > 10) else None
    if api_key:
        print("  Using BLS API key from .env")
        chunk_size = 20
        max_batch = 50
    else:
        chunk_size = 10
        max_batch = 10

    if args.series:
        series_ids = args.series
        label_map = {sid: ALL_KNOWN.get(sid, sid) for sid in series_ids}
    else:
        label_map = PRESETS[args.preset]
        series_ids = list(label_map.keys())

    print(f"\nFetching {len(series_ids)} BLS series ({args.start}–{args.end}):")
    for sid in series_ids:
        print(f"  {sid}  {label_map.get(sid, '')}")
    print()

    # Batch series into groups respecting API limits
    all_frames = []
    for i in range(0, len(series_ids), max_batch):
        batch = series_ids[i : i + max_batch]
        df_batch = fetch_range(batch, args.start, args.end, api_key, chunk_size)
        all_frames.append(df_batch)

    if not all_frames:
        sys.exit("No data returned.")

    df = all_frames[0]
    for frame in all_frames[1:]:
        df = df.join(frame, how="outer")
    df = df.sort_index()

    # Rename columns to readable labels
    df = df.rename(columns={sid: label for sid, label in label_map.items() if sid in df.columns})

    if args.out is None:
        tag = args.preset if not args.series else "custom"
        args.out = str(Path(__file__).parent.parent / ".tmp" / f"bls_{tag}_{args.start}_{args.end}.csv")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out)
    print(f"\nSaved {len(df)} rows x {len(df.columns)} series -> {args.out}")
    print(df.tail(6).to_string())


if __name__ == "__main__":
    main()
