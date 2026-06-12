"""
FRED Data Fetcher
Pulls any FRED series by ID and returns a clean pandas DataFrame.
Usage: python fred_fetch.py --series DGS10 DGS2 CPIAUCSL --start 2000-01-01
"""

import argparse
import os
import ssl
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

# Python 3.14 on Windows ships without bundled CA certs; patch the context
# so urllib can reach FRED's HTTPS endpoints. We're reading public gov data,
# risk is minimal — but document this if deploying elsewhere.
ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv(Path(__file__).parent.parent / ".env")

# Series we care about most — readable names for display
KNOWN_SERIES = {
    # Yield curve
    "DGS1MO": "Treasury 1-Month Yield",
    "DGS3MO": "Treasury 3-Month Yield",
    "DGS6MO": "Treasury 6-Month Yield",
    "DGS1": "Treasury 1-Year Yield",
    "DGS2": "Treasury 2-Year Yield",
    "DGS5": "Treasury 5-Year Yield",
    "DGS10": "Treasury 10-Year Yield",
    "DGS30": "Treasury 30-Year Yield",
    "T10Y2Y": "10Y-2Y Spread (Yield Curve)",
    "T10Y3M": "10Y-3M Spread",
    # Inflation
    "CPIAUCSL": "CPI All Items (SA)",
    "CPILFESL": "Core CPI (ex Food & Energy, SA)",
    "PCEPI": "PCE Price Index",
    "PCEPILFE": "Core PCE Price Index",
    # Growth
    "GDP": "Gross Domestic Product",
    "GDPC1": "Real GDP (Chained 2017 Dollars)",
    "INDPRO": "Industrial Production Index",
    # Labor
    "UNRATE": "Unemployment Rate",
    "PAYEMS": "Nonfarm Payrolls (Total)",
    "JTSJOL": "Job Openings (JOLTS)",
    # Money supply
    "M2SL": "M2 Money Supply",
    "M2V": "M2 Velocity",
    # Credit / financial conditions
    "BAMLH0A0HYM2": "High Yield OAS Spread",
    "TEDRATE": "TED Spread",
    "DPCREDIT": "Discount Window Primary Credit Rate",
    # Housing
    "HOUST": "Housing Starts",
    "CSUSHPINSA": "Case-Shiller Home Price Index (20-City)",
    # Dollar
    "DTWEXBGS": "Trade-Weighted USD Index (Broad)",
    "DTWEXAFEGS": "Trade-Weighted USD Index (Advanced Economies)",
    # Commodities
    "DCOILWTICO": "WTI Crude Oil Price",
    "GOLDAMGBD228NLBM": "Gold Price (London Fix, AM)",
}


def fetch(series_ids: list[str], start: str = "2000-01-01", end: str | None = None) -> pd.DataFrame:
    """
    Fetch one or more FRED series and return as a single DataFrame.
    Columns are named by series ID; rows indexed by date.
    """
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "your_fred_api_key_here":
        sys.exit("ERROR: FRED_API_KEY not set in .env — register at https://fred.stlouisfed.org/docs/api/api_key.html")

    fred = Fred(api_key=api_key)
    frames = {}

    for sid in series_ids:
        try:
            s = fred.get_series(sid, observation_start=start, observation_end=end)
            s.name = sid
            frames[sid] = s
            label = KNOWN_SERIES.get(sid, sid)
            print(f"  OK  {sid:<20} {label}  ({len(s)} observations)")
        except Exception as e:
            print(f"  FAIL {sid}: {e}", file=sys.stderr)

    if not frames:
        sys.exit("No series fetched — check series IDs and API key.")

    df = pd.DataFrame(frames)
    df.index.name = "date"
    return df


def save(df: pd.DataFrame, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path)
    print(f"\nSaved {df.shape[0]} rows x {df.shape[1]} cols -> {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch FRED series data")
    parser.add_argument("--series", nargs="+", required=True, help="FRED series IDs (e.g. DGS10 DGS2 CPIAUCSL)")
    parser.add_argument("--start", default="2000-01-01", help="Start date YYYY-MM-DD (default: 2000-01-01)")
    parser.add_argument("--end", default=None, help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--out", default=None, help="Output CSV path (default: .tmp/fred_<series>_<date>.csv)")
    args = parser.parse_args()

    print(f"\nFetching {len(args.series)} series from FRED...")
    df = fetch(args.series, start=args.start, end=args.end)

    if args.out is None:
        today = datetime.today().strftime("%Y%m%d")
        slug = "_".join(args.series[:3])
        args.out = str(Path(__file__).parent.parent / ".tmp" / f"fred_{slug}_{today}.csv")

    save(df, args.out)
    print(df.tail(5).to_string())


if __name__ == "__main__":
    main()
