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


def derive_positioning(cmf: float, threshold: float = 0.05) -> str:
    """OVER / NEUT / UNDER based on CMF value vs threshold."""
    if pd.isna(cmf):
        return "NEUT"
    if cmf > threshold:
        return "OVER"
    if cmf < -threshold:
        return "UNDER"
    return "NEUT"


def derive_alignment(pos5: str, pos15: str, pos30: str) -> tuple[int, str]:
    """
    Returns (alignment_count, arrow_string).
    alignment_count = max(over_count, under_count) — how many windows agree.
    """
    positions = [pos5, pos15, pos30]
    arrow_map = {"OVER": "▲", "UNDER": "▼", "NEUT": "→"}
    arrows = "".join(arrow_map[p] for p in positions)
    over_count = positions.count("OVER")
    under_count = positions.count("UNDER")
    return max(over_count, under_count), arrows


def compute_price_return(ohlcv: pd.DataFrame, n_days: int) -> float:
    """n-day price return from Close series. Returns nan if insufficient data."""
    closes = ohlcv["Close"].dropna()
    if len(closes) < n_days + 1:
        return float("nan")
    return float(closes.iloc[-1] / closes.iloc[-(n_days + 1)] - 1)


def derive_divergence(
    cmf15: float,
    price_return: float,
    cmf_threshold: float = 0.05,
    return_threshold: float = 0.01,
) -> str:
    """
    [DIV↓] = price rising, flow weakening (distribution signal)
    [DIV↑] = price falling, flow holding (accumulation signal)
    ""  = no divergence
    """
    if pd.isna(cmf15) or pd.isna(price_return):
        return ""
    if cmf15 < -cmf_threshold and price_return > return_threshold:
        return "[DIV↓]"
    if cmf15 > cmf_threshold and price_return < -return_threshold:
        return "[DIV↑]"
    return ""


def make_position_call(pos5: str, pos15: str, pos30: str) -> str:
    """Translate three positioning calls into a single actionable horizon string."""
    positions = [pos5, pos15, pos30]
    horizons = ["2W", "30D", "90D"]

    over_idx  = [i for i, p in enumerate(positions) if p == "OVER"]
    under_idx = [i for i, p in enumerate(positions) if p == "UNDER"]

    if len(over_idx) == 3:
        return "OVERWEIGHT  2W–90D"
    if len(under_idx) == 3:
        return "UNDERWEIGHT  2W–90D"

    # Two consecutive windows in the same direction
    for idx, label in [(over_idx, "OVERWEIGHT"), (under_idx, "UNDERWEIGHT")]:
        if len(idx) == 2 and idx[1] - idx[0] == 1:
            return f"{label}  {horizons[idx[0]]}–{horizons[idx[1]]}"

    return "HOLD / WATCH"
