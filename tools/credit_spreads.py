"""
Credit Spreads Snapshot
Fetches ICE BofA OAS series from FRED and prints a current-reading summary.

Usage:
    python tools/credit_spreads.py
    python tools/credit_spreads.py --series HY IG CCC
    python tools/credit_spreads.py --chart
    python tools/credit_spreads.py --start 2010-01-01 --chart
"""

import argparse
import os
import ssl
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

ssl._create_default_https_context = ssl._create_unverified_context

load_dotenv(Path(__file__).parent.parent / ".env")

ROOT = Path(__file__).parent.parent
TMP  = ROOT / ".tmp"

SERIES_MAP = {
    "HY":  ("BAMLH0A0HYM2", "US High Yield OAS"),
    "IG":  ("BAMLC0A0CM",   "US Investment Grade OAS"),
    "CCC": ("BAMLH0A3HYC",  "US CCC-Rated OAS"),
}

SERIES_COLORS = {
    "HY":  "#f5a623",
    "IG":  "#4a9eff",
    "CCC": "#e05c5c",
}

RECESSION_ID = "USREC"

DEFAULT_SERIES = ["HY", "IG"]
DEFAULT_START  = "2005-01-01"


def _fred() -> Fred:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "your_fred_api_key_here":
        sys.exit("ERROR: FRED_API_KEY not set in .env")
    return Fred(api_key=api_key)


def fetch_spreads(series_keys: list[str], start: str) -> pd.DataFrame:
    fred = _fred()
    frames: dict[str, pd.Series] = {}
    for key in series_keys:
        sid, label = SERIES_MAP[key]
        try:
            s = fred.get_series(sid, observation_start=start)
            s.name = key
            frames[key] = s
            print(f"  OK  {sid:<22} {label}  ({len(s)} obs)")
        except Exception as e:
            print(f"  WARN: {sid} — {e}", file=sys.stderr)
    if not frames:
        sys.exit("No series fetched.")
    return pd.DataFrame(frames)


def fetch_recessions(start: str) -> pd.Series:
    try:
        s = _fred().get_series(RECESSION_ID, observation_start=start)
        s.name = "recession"
        return s
    except Exception:
        return pd.Series(dtype=float)


def percentile_rank(series: pd.Series, value: float) -> float:
    return round((series < value).mean() * 100, 1)


def print_summary(df: pd.DataFrame, series_keys: list[str]) -> None:
    now = datetime.now().strftime("%Y-%m-%d")
    print(f"\nCredit Spread Snapshot  —  {now}")
    print("=" * 68)
    print(f"  {'Series':<26} {'Current':>8} {'52W Low':>9} {'52W High':>9} {'Pctile':>8} {'WoW Chg':>9}")
    print("-" * 68)

    one_year_ago = df.index[-1] - pd.DateOffset(years=1)

    for key in series_keys:
        if key not in df.columns:
            continue
        s = df[key].dropna()
        if s.empty:
            continue
        _, label = SERIES_MAP[key]

        current  = s.iloc[-1]
        week_ago = s.iloc[-6] if len(s) > 6 else s.iloc[0]
        wow      = current - week_ago

        s_52w    = s[s.index >= one_year_ago]
        low_52w  = s_52w.min()
        high_52w = s_52w.max()
        pctile   = percentile_rank(s, current)

        wow_str = f"{'+' if wow >= 0 else ''}{wow:.2f}"
        print(
            f"  {label:<26} {current:>7.2f}%"
            f" {low_52w:>8.2f}% {high_52w:>8.2f}%"
            f" {pctile:>7.1f}%"
            f" {wow_str:>9}"
        )

    if "HY" in df.columns and "IG" in df.columns:
        hy = df["HY"].dropna()
        ig = df["IG"].dropna()
        common = hy.index.intersection(ig.index)
        diff = hy.loc[common] - ig.loc[common]
        if not diff.empty:
            current_diff = diff.iloc[-1]
            week_ago_diff = diff.iloc[-6] if len(diff) > 6 else diff.iloc[0]
            wow_diff = current_diff - week_ago_diff
            one_year_ago = diff.index[-1] - pd.DateOffset(years=1)
            diff_52w = diff[diff.index >= one_year_ago]
            pctile_diff = percentile_rank(diff, current_diff)
            wow_str = f"{'+' if wow_diff >= 0 else ''}{wow_diff:.2f}"
            print("-" * 68)
            print(
                f"  {'HY–IG Quality Premium':<26} {current_diff:>7.2f}%"
                f" {diff_52w.min():>8.2f}% {diff_52w.max():>8.2f}%"
                f" {pctile_diff:>7.1f}%"
                f" {wow_str:>9}"
            )

    print("=" * 68)
    print("  Source: ICE BofA via FRED  |  OAS = Option-Adjusted Spread over Treasuries\n")


def make_chart(
    df: pd.DataFrame,
    series_keys: list[str],
    recessions: pd.Series,
    out_path: Path,
) -> None:
    BG = "#0a0f1e"
    GRID = "#1e2a3a"

    fig, ax = plt.subplots(figsize=(14, 7), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # Recession shading
    drew_recession = False
    if not recessions.empty:
        in_rec = False
        rec_start = None
        chart_start = df.index[0]
        chart_end   = df.index[-1]
        for date, val in recessions.items():
            if val == 1 and not in_rec:
                rec_start = date
                in_rec = True
            elif val == 0 and in_rec:
                if rec_start <= chart_end and date >= chart_start:
                    ax.axvspan(
                        max(rec_start, chart_start), min(date, chart_end),
                        color="#c0392b", alpha=0.15, zorder=0,
                    )
                    drew_recession = True
                in_rec = False
        if in_rec and rec_start is not None:
            if rec_start <= chart_end:
                ax.axvspan(
                    max(rec_start, chart_start), chart_end,
                    color="#c0392b", alpha=0.15, zorder=0,
                )
                drew_recession = True

    # Series lines
    for key in series_keys:
        if key not in df.columns:
            continue
        s = df[key].dropna()
        color = SERIES_COLORS.get(key, "#ffffff")
        _, label = SERIES_MAP[key]
        ax.plot(s.index, s.values, color=color, lw=1.8, label=label, zorder=3)
        # Current value marker
        ax.scatter([s.index[-1]], [s.iloc[-1]], color=color, s=40, zorder=4)
        ax.annotate(
            f"{s.iloc[-1]:.2f}%",
            xy=(s.index[-1], s.iloc[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            color=color,
            fontsize=9,
            fontweight="bold",
            va="center",
        )

    # Axes styling
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors="#8899aa", labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.grid(True, color=GRID, linewidth=0.6, linestyle="--", alpha=0.7)
    ax.set_xlim(df.index[0], df.index[-1])

    # Legend
    handles, labels = ax.get_legend_handles_labels()
    if drew_recession:
        rec_patch = plt.Rectangle((0, 0), 1, 1, fc="#c0392b", alpha=0.3)
        handles.append(rec_patch)
        labels.append("NBER Recession")
    ax.legend(handles, labels, framealpha=0.15, edgecolor=GRID,
              labelcolor="#cccccc", fontsize=9, loc="upper left")

    # Title
    now = datetime.now().strftime("%Y-%m-%d")
    ax.set_title(
        f"Credit Spread History  —  {now}",
        color="#e8e8e8", fontsize=13, fontweight="bold", pad=14,
    )
    ax.set_xlabel("", color="#8899aa")
    ax.set_ylabel("Option-Adjusted Spread (%)", color="#8899aa", fontsize=9)

    fig.tight_layout(pad=1.2)
    TMP.mkdir(exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG, edgecolor="none")
    plt.close()
    print(f"  Chart -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Credit spread snapshot from FRED")
    parser.add_argument(
        "--series", nargs="+", default=DEFAULT_SERIES,
        choices=list(SERIES_MAP.keys()),
        help="Spread tiers to fetch (default: HY IG)",
    )
    parser.add_argument(
        "--start", default=DEFAULT_START,
        help="History start date YYYY-MM-DD (default: 2005-01-01)",
    )
    parser.add_argument(
        "--chart", action="store_true",
        help="Save a time-series chart to .tmp/",
    )
    args = parser.parse_args()

    print(f"\nFetching credit spread data from FRED...")
    df = fetch_spreads(args.series, args.start)

    print_summary(df, args.series)

    if args.chart:
        print("Fetching recession data...")
        recessions = fetch_recessions(args.start)
        today = datetime.now().strftime("%Y%m%d")
        out = TMP / f"credit_spreads_{today}.png"
        make_chart(df, args.series, recessions, out)


if __name__ == "__main__":
    main()
