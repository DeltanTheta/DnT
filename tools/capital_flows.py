"""
Capital Flows — Multi-Timeframe Chaikin Money Flow
Fetches OHLCV for 11 SPDR sector ETFs + TLT + GLD and computes 5/15/30-day
CMF for each. Produces a ranked positioning watchlist, table, and heatmap.

CMF formula:
    MFM = ((Close - Low) - (High - Close)) / (High - Low)
    MFV = MFM × Volume
    CMF = sum(MFV, window) / sum(Volume, window)   # in [-1, +1]

Usage:
  python tools/capital_flows.py              # ranked watchlist (default)
  python tools/capital_flows.py --report     # ranked watchlist explicitly
  python tools/capital_flows.py --table      # positioning table (OVER/NEUT/UNDER grid)
  python tools/capital_flows.py --chart      # heatmap chart
  python tools/capital_flows.py --all        # all three outputs
  python tools/capital_flows.py --start 2024-01-01
  python tools/capital_flows.py --out .tmp/myfile.csv
  python tools/capital_flows.py --chart-out .tmp/myfile.png
"""

import argparse
import os
import ssl
import sys
from datetime import datetime
from pathlib import Path

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from curl_cffi import requests as curl_requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

YF_SESSION = curl_requests.Session(impersonate="chrome", verify=False)

TICKERS: dict[str, str] = {
    "XLB":  "Materials",
    "XLC":  "Comm Services",
    "XLE":  "Energy",
    "XLF":  "Financials",
    "XLI":  "Industrials",
    "XLK":  "Technology",
    "XLP":  "Consumer Staples",
    "XLRE": "Real Estate",
    "XLU":  "Utilities",
    "XLV":  "Health Care",
    "XLY":  "Consumer Discret.",
    "TLT":  "Fixed Income (proxy)",
    "GLD":  "Gold (proxy)",
}

WINDOWS: tuple[int, int, int] = (5, 15, 30)


def fetch(tickers: list[str], start: str, end: str | None) -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        try:
            df = yf.download(
                ticker, start=start, end=end,
                auto_adjust=True, progress=False, session=YF_SESSION,
            )
            if df is None or df.empty:
                print(f"  WARN: No data for {ticker}", file=sys.stderr)
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            print(f"  OK  {ticker:<5}  {len(df)} trading days  "
                  f"[{df.index[0].date()} to {df.index[-1].date()}]")
            result[ticker] = df
        except Exception as e:
            print(f"  FAIL {ticker}: {e}", file=sys.stderr)
    return result


def compute_cmf(df: pd.DataFrame, window: int) -> pd.Series:
    """Chaikin Money Flow over `window` trading days. Returns series in [-1, +1]."""
    hi, lo, cl, vol = df["High"], df["Low"], df["Close"], df["Volume"]
    hl_range = (hi - lo).replace(0, np.nan)
    mfm = ((cl - lo) - (hi - cl)) / hl_range
    mfv = mfm * vol
    return mfv.rolling(window).sum() / vol.rolling(window).sum()


def build_signal_stack(
    raw: dict[str, pd.DataFrame],
    windows: tuple[int, int, int] = WINDOWS,
) -> pd.DataFrame:
    """
    Returns wide DataFrame indexed by date.
    Columns are a MultiIndex of (ticker, window).
    """
    series: dict[tuple[str, int], pd.Series] = {}
    for ticker, ohlcv in raw.items():
        for w in windows:
            series[(ticker, w)] = compute_cmf(ohlcv, w)
    wide = pd.DataFrame(series)
    wide.columns = pd.MultiIndex.from_tuples(wide.columns, names=["ticker", "window"])
    wide.index.name = "date"
    return wide
