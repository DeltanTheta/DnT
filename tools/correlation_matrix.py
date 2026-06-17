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

import numpy as np
import pandas as pd

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


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
