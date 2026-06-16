"""
SPX Realized Volatility: 1-Month vs 3-Month
Computes and charts trailing realized vol for the S&P 500.

Two-panel output:
  Top    — Annualized 1mo and 3mo realized vol with SPX price on twin axis
  Bottom — Vol spread (1mo minus 3mo) filled above/below zero

Usage:
  python tools/spx_realized_vol.py
  python tools/spx_realized_vol.py --start 2020-01-01 --out .tmp/spx_rv.png
  python tools/spx_realized_vol.py --start 2022-01-01 --lookback 5
"""

import argparse
import os
import ssl
import sys
from datetime import datetime, timedelta
from pathlib import Path

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from curl_cffi import requests as curl_requests

YF_SESSION = curl_requests.Session(impersonate="chrome", verify=False)

COLORS = {
    "blue":   "#2563EB",
    "red":    "#DC2626",
    "green":  "#16A34A",
    "orange": "#EA580C",
    "purple": "#7C3AED",
    "gray":   "#6B7280",
}

SPREAD_POS_COLOR = "#BFDBFE"  # light blue — 1mo hotter than 3mo
SPREAD_NEG_COLOR = "#FECACA"  # light red  — term structure steepening
HEADER_BG = "#1a1a2e"


def fetch_spx(start: str) -> pd.DataFrame:
    print(f"Fetching ^GSPC from {start}...")
    df = yf.download(
        "^GSPC", start=start, auto_adjust=True,
        progress=False, session=YF_SESSION,
    )
    if df is None or df.empty:
        sys.exit("ERROR: No data returned for ^GSPC")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    print(f"  {len(df)} trading days fetched  [{df.index[0].date()} to {df.index[-1].date()}]")
    return df


def compute_vol(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["log_ret"] = np.log(df["Close"] / df["Close"].shift(1))
    df["Vol_1mo"] = df["log_ret"].rolling(22, min_periods=22).std(ddof=1)
    df["Vol_3mo"] = df["log_ret"].rolling(66, min_periods=66).std(ddof=1)
    df["AV_1mo"] = df["Vol_1mo"] * np.sqrt(252) * 100   # express as %
    df["AV_3mo"] = df["Vol_3mo"] * np.sqrt(252) * 100
    df["Vol_Diff"] = df["AV_1mo"] - df["AV_3mo"]
    df = df.dropna(subset=["AV_1mo", "AV_3mo"])
    return df


def plot(df: pd.DataFrame, out_path: str) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True,
                                    gridspec_kw={"height_ratios": [2, 1], "hspace": 0.08})

    today_str = datetime.today().strftime("%B %d, %Y")
    latest_date = df.index[-1]

    # ── Top panel: vol levels + SPX price ─────────────────────────────────────
    ax1.plot(df.index, df["AV_1mo"], label="1-Month Realized Vol",
             color=COLORS["blue"], linewidth=1.8, zorder=3)
    ax1.plot(df.index, df["AV_3mo"], label="3-Month Realized Vol",
             color=COLORS["orange"], linewidth=1.8, linestyle="--", zorder=3)

    ax1.set_ylabel("Annualized Realized Vol (%)", fontsize=11)
    ax1.tick_params(axis="y", labelsize=10)

    # SPX price on twin axis
    ax1b = ax1.twinx()
    ax1b.plot(df.index, df["Close"], label="SPX", color=COLORS["gray"],
              linewidth=1.0, alpha=0.55, zorder=1)
    ax1b.set_ylabel("SPX Level", fontsize=11, color=COLORS["gray"])
    ax1b.tick_params(axis="y", labelsize=10, labelcolor=COLORS["gray"])

    # Combined legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax1b.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=10, framealpha=0.9)

    # Annotate latest values
    rv1_last = df["AV_1mo"].iloc[-1]
    rv3_last = df["AV_3mo"].iloc[-1]
    ax1.annotate(f"{rv1_last:.1f}%", xy=(latest_date, rv1_last),
                 xytext=(6, 0), textcoords="offset points",
                 fontsize=8.5, color=COLORS["blue"], fontweight="bold")
    ax1.annotate(f"{rv3_last:.1f}%", xy=(latest_date, rv3_last),
                 xytext=(6, 0), textcoords="offset points",
                 fontsize=8.5, color=COLORS["orange"], fontweight="bold")

    # ── Bottom panel: spread filled ────────────────────────────────────────────
    spread = df["Vol_Diff"]
    ax2.plot(df.index, spread, color=COLORS["purple"], linewidth=1.4, zorder=3,
             label="1mo − 3mo Spread")
    ax2.fill_between(df.index, spread, 0,
                     where=(spread >= 0),
                     color=SPREAD_POS_COLOR, alpha=0.75, zorder=2)
    ax2.fill_between(df.index, spread, 0,
                     where=(spread < 0),
                     color=SPREAD_NEG_COLOR, alpha=0.75, zorder=2)
    ax2.axhline(0, color=COLORS["gray"], linewidth=0.9, linestyle="--", zorder=4)

    diff_last = spread.iloc[-1]
    ax2.annotate(f"{diff_last:+.1f}pp", xy=(latest_date, diff_last),
                 xytext=(6, 0), textcoords="offset points",
                 fontsize=8.5, color=COLORS["purple"], fontweight="bold")

    ax2.set_ylabel("Vol Spread (pp)", fontsize=11)
    ax2.tick_params(axis="y", labelsize=10)
    ax2.legend(loc="upper left", fontsize=10, framealpha=0.9)

    # ── X-axis formatting ─────────────────────────────────────────────────────
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    plt.setp(ax2.get_xticklabels(), rotation=45, ha="right", fontsize=10)

    # ── Titles ─────────────────────────────────────────────────────────────────
    fig.suptitle("SPX Realized Volatility: 1-Month vs 3-Month (Annualized)",
                 fontsize=14, fontweight="bold", color=HEADER_BG, y=0.98)
    ax1.set_title(
        f"As of {today_str}  |  Source: Yahoo Finance (^GSPC)  |  DeltaTheta",
        fontsize=8.5, color=COLORS["gray"], pad=4,
    )

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close()
    print(f"Chart saved -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SPX realized vol chart (1mo vs 3mo)")
    parser.add_argument("--start", default=None,
                        help="History start date YYYY-MM-DD (default: 5 years ago)")
    parser.add_argument("--lookback", type=int, default=5,
                        help="Years of history to show (default: 5, ignored if --start set)")
    parser.add_argument("--out", default=None,
                        help="Output PNG path (default: .tmp/spx_rv_<date>.png)")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    today = datetime.today()
    today_str = today.strftime("%Y%m%d")

    start = args.start or (today - timedelta(days=365 * args.lookback)).strftime("%Y-%m-%d")
    # Pull extra history so rolling windows are full at the start date
    fetch_start = (datetime.strptime(start, "%Y-%m-%d") - timedelta(days=120)).strftime("%Y-%m-%d")

    out_path = args.out or str(root / ".tmp" / f"spx_rv_{today_str}.png")

    df = fetch_spx(fetch_start)
    df = compute_vol(df)

    # Trim to requested start after windows are computed
    df = df[df.index >= start]

    print(f"\nLatest values (as of {df.index[-1].date()}):")
    print(df[["AV_1mo", "AV_3mo", "Vol_Diff"]].tail(5).to_string())

    plot(df, out_path)


if __name__ == "__main__":
    main()
