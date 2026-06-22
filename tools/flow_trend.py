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


def render_trend_chart(df: pd.DataFrame, as_of: str, out_path: str) -> None:
    """3-panel stacked chart: Cyclicals / Defensives / Macro Proxies."""
    fig, axes = plt.subplots(3, 1, figsize=(11, 13), sharex=True)
    fig.patch.set_facecolor("#F9FAFB")

    for ax, (group_name, tickers) in zip(axes, GROUPS.items()):
        ax.set_facecolor("#F9FAFB")
        ax.axhline(0, color="#9CA3AF", linewidth=0.8, linestyle="--")
        for ticker in tickers:
            col = f"{ticker}_cmf30"
            if col not in df.columns:
                continue
            series = df[col].dropna()
            ax.plot(series.index, series.values, linewidth=1.5, label=LABELS[ticker])
        ax.set_ylabel("30D CMF", fontsize=9, color="#374151")
        ax.set_title(group_name, fontsize=10, fontweight="bold",
                     color="#111827", pad=6)
        ax.legend(fontsize=8, loc="upper left", framealpha=0.7)
        ax.tick_params(axis="both", labelsize=8, colors="#374151")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_ylim(-0.5, 0.5)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate(rotation=30, ha="right")

    fig.suptitle(
        f"Capital Flow Trends  |  30-Day CMF  |  As of {as_of}",
        fontsize=12, fontweight="bold", color="#111827", y=1.01,
    )
    fig.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flow Trend — 30-day CMF time-series chart (3 panels)"
    )
    parser.add_argument("--lookback", type=int, default=60,
                        help="Trading days of history to plot (default: 60)")
    parser.add_argument("--csv", default=None,
                        help="Path to capital_flows CSV (default: latest in .tmp/)")
    parser.add_argument("--out", default=None,
                        help="Output PNG path (default: .tmp/flow_trend_<date>.png)")
    args = parser.parse_args()

    tmp_dir = str(Path(__file__).parent.parent / ".tmp")
    csv_path = args.csv or find_latest_csv(tmp_dir)
    today_str = datetime.today().strftime("%Y%m%d")
    out_path = args.out or str(Path(tmp_dir) / f"flow_trend_{today_str}.png")

    df = load_csv(csv_path)
    df = slice_lookback(df, args.lookback)

    as_of = str(df.index[-1].date())
    print(f"\nFlow Trend Chart  —  {as_of}  ({args.lookback}-day lookback)")
    render_trend_chart(df, as_of=as_of, out_path=out_path)


if __name__ == "__main__":
    main()
