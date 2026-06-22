"""
Sector Money Flow — 15-day Chaikin Money Flow (CMF)
Fetches OHLCV for the 11 SPDR sector ETFs plus TLT (fixed income proxy) and
GLD (gold proxy), then computes 15-day CMF for each.

CMF formula (per bar):
    MFM = ((Close - Low) - (High - Close)) / (High - Low)   # Money Flow Multiplier
    MFV = MFM * Volume                                        # Money Flow Volume
    CMF = sum(MFV, window) / sum(Volume, window)             # -1 to +1

Note: these are indicative of broader asset-class flows, not precise sector
accounting — each ticker is the exact ETF measured, not the full sector market cap.

Usage:
  python tools/sector_money_flow.py
  python tools/sector_money_flow.py --start 2024-01-01
  python tools/sector_money_flow.py --window 20 --out .tmp/cmf_20d.csv
  python tools/sector_money_flow.py --chart
  python tools/sector_money_flow.py --chart --chart-out .tmp/cmf_chart.png
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

TICKERS = {
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
    "XLY":  "Consumer Discretionary",
    "TLT":  "Fixed Income (proxy)",
    "GLD":  "Gold (proxy)",
}

DEFAULT_WINDOW = 15


def fetch(tickers: list[str], start: str, end: str | None) -> dict[str, pd.DataFrame]:
    result = {}
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
    hl_range = (hi - lo).replace(0, np.nan)            # avoid div/0 on doji bars
    mfm = ((cl - lo) - (hi - cl)) / hl_range           # Money Flow Multiplier
    mfv = mfm * vol                                     # Money Flow Volume
    cmf = mfv.rolling(window).sum() / vol.rolling(window).sum()
    return cmf


def build_summary(raw: dict[str, pd.DataFrame], window: int) -> pd.DataFrame:
    """
    Returns a wide DataFrame indexed by date with one column per ticker (CMF values),
    plus a long-format snapshot of the most recent row for easy inspection.
    """
    cmf_series = {}
    for ticker, ohlcv in raw.items():
        cmf_series[ticker] = compute_cmf(ohlcv, window)

    wide = pd.DataFrame(cmf_series)
    wide.index.name = "date"
    return wide


def latest_snapshot(wide: pd.DataFrame) -> pd.DataFrame:
    """Most recent CMF values, sorted descending (most positive flow first)."""
    last = wide.dropna(how="all").iloc[-1].rename("cmf_15d")
    df = last.to_frame().reset_index().rename(columns={"index": "ticker"})
    df["label"] = df["ticker"].map(TICKERS)
    df = df.sort_values("cmf_15d", ascending=False).reset_index(drop=True)
    df["cmf_15d"] = df["cmf_15d"].round(4)
    return df[["ticker", "label", "cmf_15d"]]


COLOR_POS = "#2563EB"   # blue — inflow
COLOR_NEG = "#DC2626"   # red  — outflow
COLOR_ZERO = "#6B7280"  # gray — near zero


def render_chart(snap: pd.DataFrame, window: int, as_of: str, out_path: str) -> None:
    """Horizontal bar chart of CMF snapshot, sorted positive→negative."""
    labels = snap["label"].tolist()
    values = snap["cmf_15d"].tolist()
    colors = [COLOR_POS if v >= 0 else COLOR_NEG for v in values]

    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor("#F9FAFB")
    ax.set_facecolor("#F9FAFB")

    bars = ax.barh(labels, values, color=colors, height=0.6, zorder=2)

    ax.axvline(0, color=COLOR_ZERO, linewidth=0.8, zorder=3)
    ax.set_xlabel(f"{window}-Day Chaikin Money Flow", fontsize=10, color="#374151")
    ax.set_title(
        f"Sector Money Flow  |  {window}-Day CMF  |  As of {as_of}",
        fontsize=12, fontweight="bold", color="#111827", pad=12,
    )

    ax.tick_params(colors="#374151", labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.xaxis.grid(True, color="#E5E7EB", linewidth=0.6, zorder=1)
    ax.set_axisbelow(True)

    note = "ETF proxies only — indicative of broader flows, not precise sector accounting."
    fig.text(0.5, -0.02, note, ha="center", fontsize=7.5, color="#9CA3AF",
             style="italic")

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved -> {out_path}")


def save(df: pd.DataFrame, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path)
    print(f"\nSaved {df.shape[0]} rows x {df.shape[1]} cols -> {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="15-day Chaikin Money Flow for SPX sectors + TLT + GLD"
    )
    parser.add_argument("--start", default="2023-01-01",
                        help="Start date YYYY-MM-DD (default: 2023-01-01)")
    parser.add_argument("--end", default=None,
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW,
                        help=f"CMF window in trading days (default: {DEFAULT_WINDOW})")
    parser.add_argument("--out", default=None,
                        help="Output CSV path (default: .tmp/sector_cmf_<date>.csv)")
    parser.add_argument("--chart", action="store_true",
                        help="Generate a bar chart of the latest CMF snapshot")
    parser.add_argument("--chart-out", default=None,
                        help="Chart PNG path (default: .tmp/sector_cmf_chart_<date>.png)")
    args = parser.parse_args()

    print(f"\nFetching OHLCV for {len(TICKERS)} tickers...")
    raw = fetch(list(TICKERS.keys()), start=args.start, end=args.end)

    if not raw:
        sys.exit("No data fetched.")

    print(f"\nComputing {args.window}-day CMF...")
    wide = build_summary(raw, window=args.window)

    today_str = datetime.today().strftime("%Y%m%d")
    out_path = args.out or str(
        Path(__file__).parent.parent / ".tmp" / f"sector_cmf_{today_str}.csv"
    )
    save(wide, out_path)

    snap = latest_snapshot(wide)
    as_of = str(wide.dropna(how="all").index[-1].date())
    print(f"\n--- Latest {args.window}-day CMF snapshot ({as_of}) ---")
    print(snap.to_string(index=False))

    if args.chart:
        chart_path = args.chart_out or str(
            Path(__file__).parent.parent / ".tmp" / f"sector_cmf_chart_{today_str}.png"
        )
        render_chart(snap, window=args.window, as_of=as_of, out_path=chart_path)


if __name__ == "__main__":
    main()
