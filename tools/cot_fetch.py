"""
CFTC Commitments of Traders (COT) Fetcher
Downloads the legacy COT report from cftc.gov and extracts net positioning
for one or more futures markets.

No API key required — CFTC publishes bulk CSV/ZIP downloads publicly.

Usage:
    # Single market — S&P 500 futures
    python tools/cot_fetch.py --market "S&P 500" --out .tmp/cot_sp500.csv

    # Multiple markets
    python tools/cot_fetch.py --market "S&P 500" "GOLD" "EURO FX" --out .tmp/cot_multi.csv

    # List all available market names in the dataset
    python tools/cot_fetch.py --list-markets

    # Use cached local ZIP instead of re-downloading
    python tools/cot_fetch.py --market "10-YEAR T-NOTES" --zip .tmp/cot_raw.zip
"""

import argparse
import io
import ssl
import sys
import warnings
import zipfile
from pathlib import Path

import pandas as pd
import requests
import urllib3

# Python 3.14 on Windows ships without bundled CA certs — same fix as fred_fetch.py
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

COT_HISTORY_URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"

# Column name map — TFF (Traders in Financial Futures) disaggregated format
# Leveraged Money = hedge funds, CTAs (trend-following speculators)
# Asset Manager   = pension funds, mutual funds, endowments (institutional)
# Dealer          = banks, swap dealers (intermediaries)
COL_MAP = {
    "Market_and_Exchange_Names":        "market",
    "Report_Date_as_YYYY-MM-DD":        "date",
    "Open_Interest_All":                "open_interest",
    "Lev_Money_Positions_Long_All":     "lev_long",
    "Lev_Money_Positions_Short_All":    "lev_short",
    "Asset_Mgr_Positions_Long_All":     "am_long",
    "Asset_Mgr_Positions_Short_All":    "am_short",
    "Dealer_Positions_Long_All":        "dealer_long",
    "Dealer_Positions_Short_All":       "dealer_short",
    "NonRept_Positions_Long_All":       "nr_long",
    "NonRept_Positions_Short_All":      "nr_short",
}

# Well-known market name fragments → canonical labels
KNOWN_MARKETS = {
    "S&P 500":        "S&P 500 FUTURES",
    "E-MINI S&P":     "S&P 500 FUTURES",
    "NASDAQ":         "NASDAQ FUTURES",
    "10-YEAR":        "10-YEAR T-NOTE FUTURES",
    "5-YEAR":         "5-YEAR T-NOTE FUTURES",
    "2-YEAR":         "2-YEAR T-NOTE FUTURES",
    "30-YEAR":        "30-YEAR T-BOND FUTURES",
    "EURO FX":        "EURO FX FUTURES",
    "JAPANESE YEN":   "JAPANESE YEN FUTURES",
    "GOLD":           "GOLD FUTURES",
    "CRUDE OIL":      "CRUDE OIL FUTURES",
    "WTI":            "CRUDE OIL FUTURES",
    "COPPER":         "COPPER FUTURES",
    "VIX":            "VIX FUTURES",
}


def download_zip(url: str, cache_path: Path | None = None) -> bytes:
    if cache_path and cache_path.exists():
        print(f"  Using cached file: {cache_path}")
        return cache_path.read_bytes()
    print(f"  Downloading: {url}")
    r = requests.get(url, timeout=60, verify=False)
    r.raise_for_status()
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(r.content)
        print(f"  Cached -> {cache_path}")
    return r.content


def load_cot_df(zip_bytes: bytes) -> pd.DataFrame:
    """Extract and parse the COT CSV from a CFTC ZIP archive."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        # CFTC ZIPs contain a single .txt or .csv file
        names = zf.namelist()
        csv_name = next((n for n in names if n.endswith((".txt", ".csv"))), names[0])
        with zf.open(csv_name) as f:
            df = pd.read_csv(f, low_memory=False)

    # Normalize column names (strip whitespace, replace spaces)
    df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("/", "_")

    # Keep only columns we care about (allow missing columns gracefully)
    keep = {k: v for k, v in COL_MAP.items() if k in df.columns}
    if "date" not in keep.values():
        sys.exit(f"ERROR: Could not find date column. Available columns:\n{list(df.columns)}")

    df = df[list(keep.keys())].rename(columns=keep)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    # Derived net positioning columns
    for col in ["lev_long", "lev_short", "am_long", "am_short",
                "dealer_long", "dealer_short", "nr_long", "nr_short"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["lev_net"]    = df["lev_long"]    - df["lev_short"]     # hedge funds net
    df["am_net"]     = df["am_long"]     - df["am_short"]      # institutional net
    df["dealer_net"] = df["dealer_long"] - df["dealer_short"]  # dealer net
    df["nr_net"]     = df["nr_long"]     - df["nr_short"]

    return df


def filter_market(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """Return rows matching market name (case-insensitive substring)."""
    # Prefer exact exchange suffix match over cross-rate (e.g. "EURO FX" -> EUR/USD not EUR/GBP)
    mask = df["market"].str.upper().str.contains(query.upper(), na=False)
    candidates = df[mask].copy()
    # Prefer entries without "/" in the market name (outright contracts over cross-rates)
    outright = candidates[~candidates["market"].str.contains("/", na=False)]
    result = outright if not outright.empty else candidates
    if result.empty:
        # Try KNOWN_MARKETS lookup
        for k, v in KNOWN_MARKETS.items():
            if query.upper() in k.upper() or k.upper() in query.upper():
                mask = df["market"].str.upper().str.contains(k.upper(), na=False)
                result = df[mask].copy()
                break
    return result


def list_markets(df: pd.DataFrame) -> None:
    markets = df["market"].dropna().unique()
    print(f"\n{len(markets)} markets in dataset:\n")
    for m in sorted(markets):
        print(f"  {m}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch CFTC COT positioning data")
    parser.add_argument("--market", nargs="+", help="Market name fragment(s) to extract (e.g. 'S&P 500' 'GOLD')")
    parser.add_argument("--year", type=int, default=2024, help="Year to fetch (default: 2024)")
    parser.add_argument("--zip", default=None, help="Path to cached local ZIP (skips download)")
    parser.add_argument("--out", default=None, help="Output CSV path")
    parser.add_argument("--list-markets", action="store_true", dest="list_markets",
                        help="Print all available market names and exit")
    args = parser.parse_args()

    if not args.market and not args.list_markets:
        parser.error("Specify --market or --list-markets")

    cache_path = Path(args.zip) if args.zip else Path(__file__).parent.parent / ".tmp" / f"cot_txt_{args.year}.zip"
    url = COT_HISTORY_URL.format(year=args.year)

    print(f"\nLoading COT data ({args.year})...")
    zip_bytes = download_zip(url, cache_path)
    df = load_cot_df(zip_bytes)
    print(f"  Loaded {len(df):,} rows across {df['market'].nunique()} markets")

    if args.list_markets:
        list_markets(df)
        return

    results = []
    for query in args.market:
        match = filter_market(df, query)
        if match.empty:
            print(f"  WARN: No market found matching '{query}' — use --list-markets to browse")
            continue
        market_name = match["market"].iloc[0]
        print(f"  OK  '{query}' -> {market_name}  ({len(match)} weeks)")
        match = match.copy()
        match["market_label"] = query
        results.append(match)

    if not results:
        sys.exit("No data extracted — check market names with --list-markets")

    out_df = pd.concat(results).reset_index(drop=True)
    out_cols = ["date", "market", "market_label", "open_interest",
                "lev_net", "am_net", "dealer_net", "nr_net",
                "lev_long", "lev_short", "am_long", "am_short",
                "dealer_long", "dealer_short"]
    out_df = out_df[[c for c in out_cols if c in out_df.columns]]

    if args.out is None:
        slug = "_".join(args.market[:2]).replace(" ", "_").replace("&", "").replace("/", "")[:30]
        args.out = str(Path(__file__).parent.parent / ".tmp" / f"cot_{slug}_{args.year}.csv")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.out, index=False)
    print(f"\nSaved {len(out_df)} rows -> {args.out}")
    print(out_df[["date", "market_label", "lev_net", "am_net", "dealer_net"]].tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
