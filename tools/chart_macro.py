"""
Macro Chart Generator
Produces publication-quality time-series charts from FRED CSV output.

Usage examples:
  # Yield curve — dual axis (yields left, spread right with fill)
  python tools/chart_macro.py --csv .tmp/fred_DGS2_DGS10_T10Y2Y_20260611.csv \
      --left DGS2 DGS10 --right T10Y2Y --fill-zero T10Y2Y \
      --title "US Yield Curve: 2Y vs 10Y and Spread" --out .tmp/yield_curve.png

  # Single series
  python tools/chart_macro.py --csv .tmp/fred_CPIAUCSL_20260611.csv \
      --left CPIAUCSL --title "CPI All Items" --out .tmp/cpi.png

  # With recession shading (fetches USREC from FRED automatically)
  python tools/chart_macro.py --csv .tmp/fred_DGS2_DGS10_T10Y2Y_20260611.csv \
      --left DGS2 DGS10 --right T10Y2Y --fill-zero T10Y2Y \
      --recessions --title "Yield Curve with Recessions" --out .tmp/yield_curve_rec.png
"""

import argparse
import os
import ssl
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

ssl._create_default_https_context = ssl._create_unverified_context

# ── Style ─────────────────────────────────────────────────────────────────────
COLORS = {
    "blue":   "#2563EB",
    "red":    "#DC2626",
    "green":  "#16A34A",
    "orange": "#EA580C",
    "purple": "#7C3AED",
    "gray":   "#6B7280",
}
LINE_COLORS = list(COLORS.values())

RECESSION_COLOR = "#D1D5DB"  # light gray fill for recession bands
SPREAD_POS_COLOR = "#BFDBFE"  # light blue — curve normal
SPREAD_NEG_COLOR = "#FECACA"  # light red — curve inverted


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col="date", parse_dates=True)
    df = df.sort_index()
    return df


def fetch_recessions(start: str, end: str) -> list[tuple]:
    """Return list of (start, end) datetime pairs for NBER recessions from FRED."""
    try:
        from fredapi import Fred
        api_key = os.getenv("FRED_API_KEY")
        if not api_key or api_key == "your_fred_api_key_here":
            print("  WARN: FRED_API_KEY not set — skipping recession shading")
            return []
        fred = Fred(api_key=api_key)
        usrec = fred.get_series("USREC", observation_start=start, observation_end=end)
        # Find contiguous recession periods
        in_rec = False
        bands = []
        rec_start = None
        for date, val in usrec.items():
            if val == 1 and not in_rec:
                rec_start = date
                in_rec = True
            elif val == 0 and in_rec:
                bands.append((rec_start, date))
                in_rec = False
        if in_rec:
            bands.append((rec_start, usrec.index[-1]))
        print(f"  Recession bands: {len(bands)} periods fetched from FRED")
        return bands
    except Exception as e:
        print(f"  WARN: Could not fetch recession data: {e}")
        return []


def plot(
    df: pd.DataFrame,
    left_cols: list[str],
    right_cols: list[str],
    fill_zero_col: str | None,
    recession_bands: list[tuple],
    title: str,
    left_label: str,
    right_label: str,
    out_path: str,
) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax1 = plt.subplots(figsize=(14, 6))

    color_cycle = iter(LINE_COLORS)

    # ── Recession shading (behind everything) ─────────────────────────────
    for rec_start, rec_end in recession_bands:
        ax1.axvspan(rec_start, rec_end, color=RECESSION_COLOR, alpha=0.6, zorder=0)

    # ── Left axis series ──────────────────────────────────────────────────
    for col in left_cols:
        if col not in df.columns:
            print(f"  WARN: column '{col}' not in CSV — skipping")
            continue
        color = next(color_cycle)
        ax1.plot(df.index, df[col], label=col, color=color, linewidth=1.6, zorder=2)

    ax1.set_ylabel(left_label, fontsize=11)
    ax1.tick_params(axis="y", labelsize=10)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax1.xaxis.set_major_locator(mdates.YearLocator(2))
    plt.xticks(rotation=45, ha="right")

    # ── Right axis series ─────────────────────────────────────────────────
    ax2 = None
    if right_cols:
        ax2 = ax1.twinx()
        for col in right_cols:
            if col not in df.columns:
                print(f"  WARN: column '{col}' not in CSV — skipping")
                continue
            color = next(color_cycle)

            if col == fill_zero_col:
                # Fill above/below zero with different colors
                series = df[col].dropna()
                ax2.plot(series.index, series.values, color=COLORS["gray"],
                         linewidth=1.2, label=col, zorder=3)
                ax2.fill_between(
                    series.index, series.values, 0,
                    where=(series.values >= 0),
                    color=SPREAD_POS_COLOR, alpha=0.7, zorder=1, label="_normal"
                )
                ax2.fill_between(
                    series.index, series.values, 0,
                    where=(series.values < 0),
                    color=SPREAD_NEG_COLOR, alpha=0.7, zorder=1, label="_inverted"
                )
                ax2.axhline(0, color=COLORS["gray"], linewidth=0.8, linestyle="--", zorder=2)
            else:
                ax2.plot(df.index, df[col], label=col, color=color,
                         linewidth=1.4, linestyle="--", zorder=2)

        ax2.set_ylabel(right_label, fontsize=11)
        ax2.tick_params(axis="y", labelsize=10)

    # ── Legend — combine both axes ────────────────────────────────────────
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = (ax2.get_legend_handles_labels() if ax2 else ([], []))
    all_handles = handles1 + [h for h, l in zip(handles2, labels2) if not l.startswith("_")]
    all_labels = labels1 + [l for l in labels2 if not l.startswith("_")]
    ax1.legend(all_handles, all_labels, loc="upper left", fontsize=10, framealpha=0.9)

    # ── Annotations ───────────────────────────────────────────────────────
    latest = df.dropna(how="all").index[-1]
    for col in left_cols:
        if col in df.columns and not pd.isna(df[col].iloc[-1]):
            val = df[col].dropna().iloc[-1]
            ax1.annotate(f"{val:.2f}%", xy=(latest, val),
                         xytext=(6, 0), textcoords="offset points",
                         fontsize=8, color=COLORS["gray"])

    # ── Title and source ──────────────────────────────────────────────────
    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.01)
    ax1.set_title(f"Source: FRED, St. Louis Federal Reserve  |  DeltaTheta",
                  fontsize=8, color=COLORS["gray"], pad=4)

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Chart saved -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate macro time-series charts")
    parser.add_argument("--csv", required=True, help="Input CSV from fred_fetch.py")
    parser.add_argument("--left", nargs="+", default=[], help="Columns for left y-axis")
    parser.add_argument("--right", nargs="+", default=[], help="Columns for right y-axis")
    parser.add_argument("--fill-zero", dest="fill_zero", default=None,
                        help="Column to fill above/below zero (spread visualization)")
    parser.add_argument("--recessions", action="store_true",
                        help="Shade NBER recession periods (fetches USREC from FRED)")
    parser.add_argument("--title", default="Macro Chart", help="Chart title")
    parser.add_argument("--left-label", dest="left_label", default="Yield (%)")
    parser.add_argument("--right-label", dest="right_label", default="Spread (pp)")
    parser.add_argument("--start", default=None, help="Trim to start date YYYY-MM-DD")
    parser.add_argument("--out", default=None, help="Output PNG path")
    args = parser.parse_args()

    if not args.left and not args.right:
        sys.exit("ERROR: specify at least one column with --left or --right")

    df = load_csv(args.csv)
    if args.start:
        df = df[df.index >= args.start]

    date_range = (str(df.index[0].date()), str(df.index[-1].date()))
    print(f"Loaded {len(df)} rows  [{date_range[0]} to {date_range[1]}]")

    recession_bands = []
    if args.recessions:
        recession_bands = fetch_recessions(date_range[0], date_range[1])

    if args.out is None:
        slug = "_".join((args.left + args.right)[:3])
        args.out = str(Path(__file__).parent.parent / ".tmp" / f"chart_{slug}.png")

    plot(
        df=df,
        left_cols=args.left,
        right_cols=args.right,
        fill_zero_col=args.fill_zero,
        recession_bands=recession_bands,
        title=args.title,
        left_label=args.left_label,
        right_label=args.right_label,
        out_path=args.out,
    )


if __name__ == "__main__":
    main()
