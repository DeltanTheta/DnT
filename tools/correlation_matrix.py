"""
Correlation Matrix — Macro Asset Proxies
Computes and visualizes a 63-day rolling correlation matrix for a configurable
set of tickers, showing current snapshot, 1-week-prior snapshot, and the delta.

Usage:
  python tools/correlation_matrix.py
  python tools/correlation_matrix.py --tickers SPY QQQ TLT GLD --window 63
  python tools/correlation_matrix.py --labels DX-Y.NYB:DXY IEF:10Y

Requires: yfinance>=0.2.0 seaborn matplotlib pandas numpy curl_cffi
"""

import os
import ssl
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
import yfinance as yf
from curl_cffi import requests as curl_requests

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(Path(__file__).parent.parent / ".env")

YF_SESSION = curl_requests.Session(impersonate="chrome", verify=False)


DEFAULT_TICKERS = ["SPY", "IWM", "QQQ", "TLT", "IEF", "GLD", "DX-Y.NYB"]
DEFAULT_LABELS: dict[str, str] = {"DX-Y.NYB": "DXY"}


def compute_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Compute daily log returns. Drops the first NaN row."""
    return np.log(prices / prices.shift(1)).dropna()


def correlation_window(returns: pd.DataFrame, end_offset: int, window: int) -> pd.DataFrame:
    """
    Compute Pearson correlation matrix over a trailing window of returns.

    end_offset=0  → window ends at the last row (current snapshot)
    end_offset=5  → window ends 5 rows before the last (prior snapshot)
    """
    if end_offset == 0:
        window_returns = returns.iloc[-window:]
    else:
        window_returns = returns.iloc[-(window + end_offset):-end_offset]
    return window_returns.corr()


def fetch_closes(tickers: list[str], start: str, end: str | None) -> pd.DataFrame:
    """Download adjusted close prices for all tickers. Returns wide DataFrame (date × ticker)."""
    frames: dict[str, pd.Series] = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start, end=end, auto_adjust=True,
                             progress=False, session=YF_SESSION)
            if df is None or df.empty:
                print(f"  WARN: No data for {ticker}", file=sys.stderr)
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            frames[ticker] = df["Close"]
            print(f"  OK  {ticker:<12}  {len(df)} trading days  "
                  f"[{df.index[0].date()} to {df.index[-1].date()}]")
        except Exception as e:
            print(f"  FAIL {ticker}: {e}", file=sys.stderr)

    if not frames:
        return pd.DataFrame()

    prices = pd.DataFrame(frames)
    prices.index.name = "date"
    return prices


def print_top_movers(current: pd.DataFrame, prior: pd.DataFrame, n: int = 5) -> None:
    """Print the top n ticker pairs ranked by absolute correlation change."""
    if current.columns.tolist() != prior.columns.tolist():
        raise ValueError("current and prior correlation matrices must have identical columns")
    delta = current - prior
    tickers = list(current.columns)
    pairs = []
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            a, b = tickers[i], tickers[j]
            d = delta.loc[a, b]
            if pd.isna(d):
                continue
            c = current.loc[a, b]
            p = prior.loc[a, b]
            pairs.append((abs(d), a, b, p, c, d))
    pairs.sort(reverse=True)
    print(f"\nTop {n} movers (prior → current):")
    for _, a, b, p, c, d in pairs[:n]:
        sign = "+" if d >= 0 else ""
        print(f"  {a} / {b:<14}  {p:+.2f} → {c:+.2f}  ({sign}{d:.2f})")
