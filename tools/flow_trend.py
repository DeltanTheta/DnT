"""
Flow Trend — 30-Day CMF Time-Series Chart
Reads the latest capital_flows CSV from .tmp/ and produces a 3-panel
trend chart: Cyclicals / Defensives / Macro Proxies.

Usage:
  python tools/flow_trend.py
  python tools/flow_trend.py --lookback 90
  python tools/flow_trend.py --csv .tmp/capital_flows_20260622.csv
  python tools/flow_trend.py --out .tmp/myfile.png
"""

import argparse
import glob
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # used by render_trend_chart (Task 2)
import matplotlib.dates as mdates  # used by render_trend_chart (Task 2)
import pandas as pd

GROUPS: dict[str, list[str]] = {
    "Cyclicals":     ["XLE", "XLI", "XLB", "XLY", "XLK"],
    "Defensives":    ["XLP", "XLU", "XLV", "XLRE", "XLC"],
    "Macro Proxies": ["XLF", "TLT", "GLD"],
}

LABELS: dict[str, str] = {
    "XLE":  "Energy",
    "XLI":  "Industrials",
    "XLB":  "Materials",
    "XLY":  "Consumer Discret.",
    "XLK":  "Technology",
    "XLP":  "Consumer Staples",
    "XLU":  "Utilities",
    "XLV":  "Health Care",
    "XLRE": "Real Estate",
    "XLC":  "Comm Services",
    "XLF":  "Financials",
    "TLT":  "Fixed Income (proxy)",
    "GLD":  "Gold (proxy)",
}


def find_latest_csv(tmp_dir: str) -> str:
    matches = sorted(glob.glob(str(Path(tmp_dir) / "capital_flows_*.csv")))
    if not matches:
        sys.exit(f"No capital_flows_*.csv found in {tmp_dir}. Run capital_flows.py first.")
    return matches[-1]


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index.name = "date"
    return df


def slice_lookback(df: pd.DataFrame, n: int) -> pd.DataFrame:
    return df.iloc[-n:]
