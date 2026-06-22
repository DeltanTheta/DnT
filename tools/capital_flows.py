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


def derive_snapshot(
    wide: pd.DataFrame,
    raw: dict[str, pd.DataFrame],
    tickers: dict[str, str],
    windows: tuple[int, int, int] = WINDOWS,
) -> pd.DataFrame:
    """
    Builds a one-row-per-ticker snapshot from the latest date in `wide`.
    Sorted by 15-day CMF descending (strongest inflow first).
    """
    filtered = wide.dropna(how="all")
    if filtered.empty:
        return pd.DataFrame()
    last = filtered.iloc[-1]
    w5, w15, w30 = windows
    rows = []
    for ticker, label in tickers.items():
        if ticker not in raw:
            continue
        cmf5  = float(last.get((ticker, w5),  float("nan")))
        cmf15 = float(last.get((ticker, w15), float("nan")))
        cmf30 = float(last.get((ticker, w30), float("nan")))
        pos5  = derive_positioning(cmf5)
        pos15 = derive_positioning(cmf15)
        pos30 = derive_positioning(cmf30)
        align_count, align_arrows = derive_alignment(pos5, pos15, pos30)
        ret15 = compute_price_return(raw[ticker], w15)
        div_flag = derive_divergence(cmf15, ret15)
        position_call = make_position_call(pos5, pos15, pos30)
        rows.append({
            "ticker": ticker,
            "label": label,
            "cmf5":  round(cmf5,  4),
            "cmf15": round(cmf15, 4),
            "cmf30": round(cmf30, 4),
            "pos5":  pos5,
            "pos15": pos15,
            "pos30": pos30,
            "align_count":    align_count,
            "align_arrows":   align_arrows,
            "price_return_15d": round(ret15, 4) if not np.isnan(ret15) else float("nan"),
            "div_flag":       div_flag,
            "position_call":  position_call,
        })
    snap = pd.DataFrame(rows)
    return snap.sort_values("cmf15", ascending=False).reset_index(drop=True)


def _fmt_cmf(v) -> str:
    return f"{v:>+7.4f}" if not pd.isna(v) else "    ---"


def print_watchlist(snap: pd.DataFrame, as_of: str) -> None:
    """Prints ranked watchlist — primary output, anchor format."""
    print(f"\nCapital Flow Watchlist  —  {as_of}")
    print("Horizon: 2W / 30D / 90D\n")
    header = f"  {'Sector':<24}  {'5D':>7}  {'15D':>7}  {'30D':>7}  {'Align':>5}  Position"
    print(header)
    print("  " + "─" * 78)
    for _, row in snap.iterrows():
        div = f"  {row['div_flag']}" if row["div_flag"] else ""
        line = (
            f"  {row['label']:<24}"
            f"  {_fmt_cmf(row['cmf5'])}"
            f"  {_fmt_cmf(row['cmf15'])}"
            f"  {_fmt_cmf(row['cmf30'])}"
            f"  {row['align_arrows']:>5}"
            f"  {row['position_call']}{div}"
        )
        print(line)
    print()


def print_table(snap: pd.DataFrame, as_of: str) -> None:
    """Prints sector × timeframe positioning grid (OVER/NEUT/UNDER)."""
    print(f"\nPositioning Table  —  {as_of}\n")
    header = f"  {'Sector':<24}  {'2W':>6}  {'30D':>6}  {'90D':>6}"
    print(header)
    print("  " + "─" * 48)
    for _, row in snap.iterrows():
        print(
            f"  {row['label']:<24}"
            f"  {row['pos5']:>6}"
            f"  {row['pos15']:>6}"
            f"  {row['pos30']:>6}"
        )
    print()


def render_heatmap(snap: pd.DataFrame, as_of: str, out_path: str) -> None:
    """
    Heatmap: rows = sectors (sorted by 15D CMF), columns = 5D/15D/30D windows.
    Blue = inflow, red = outflow, intensity = magnitude. Divergence cells marked.
    """
    labels = snap["label"].tolist()
    data = snap[["cmf5", "cmf15", "cmf30"]].values.astype(float)
    vmax = 0.30  # clip colorscale; typical CMF range is well within ±0.3

    fig, ax = plt.subplots(figsize=(7, max(5, len(labels) * 0.55 + 1.5)))
    fig.patch.set_facecolor("#F9FAFB")
    ax.set_facecolor("#F9FAFB")

    im = ax.imshow(data, cmap="RdBu", vmin=-vmax, vmax=vmax, aspect="auto")

    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["5D (2W)", "15D (30D)", "30D (90D)"], fontsize=10, color="#374151")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9, color="#374151")

    for i in range(len(labels)):
        for j in range(3):
            val = data[i, j]
            if np.isnan(val):
                continue
            text_color = "white" if abs(val) > 0.15 else "#111827"
            ax.text(j, i, f"{val:+.3f}", ha="center", va="center",
                    fontsize=8, color=text_color)
        # Mark divergence on the 15D column (index 1)
        if snap.iloc[i]["div_flag"]:
            ax.text(1.42, i - 0.38, "D", fontsize=6.5, color="#F59E0B",
                    fontweight="bold")

    ax.set_title(
        f"Capital Flow Heatmap  |  5 / 15 / 30-Day CMF  |  As of {as_of}",
        fontsize=12, fontweight="bold", color="#111827", pad=12,
    )
    plt.colorbar(im, ax=ax, label="CMF", shrink=0.6, pad=0.02)

    note = "ETF proxies only — indicative of broader flows, not precise sector accounting."
    fig.text(0.5, -0.01, note, ha="center", fontsize=7.5, color="#9CA3AF", style="italic")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved → {out_path}")


def save(wide: pd.DataFrame, path: str) -> None:
    """Saves flattened wide CMF time series to CSV. Columns: XLF_cmf5, XLF_cmf15, ..."""
    flat = wide.set_axis([f"{t}_cmf{w}" for t, w in wide.columns], axis="columns")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    flat.to_csv(path)
    print(f"\nSaved {flat.shape[0]} rows × {flat.shape[1]} cols → {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capital Flows — multi-timeframe CMF for SPX sectors + TLT + GLD"
    )
    parser.add_argument("--report", action="store_true",
                        help="Print ranked watchlist (default if no output flag given)")
    parser.add_argument("--table",  action="store_true",
                        help="Print positioning table (OVER/NEUT/UNDER grid)")
    parser.add_argument("--chart",  action="store_true",
                        help="Generate heatmap chart PNG")
    parser.add_argument("--all",    action="store_true",
                        help="All three outputs: watchlist + table + chart")
    parser.add_argument("--start",  default="2023-01-01",
                        help="Start date YYYY-MM-DD (default: 2023-01-01)")
    parser.add_argument("--end",    default=None,
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--out",    default=None,
                        help="CSV output path (default: .tmp/capital_flows_<date>.csv)")
    parser.add_argument("--chart-out", default=None,
                        help="Chart PNG path (default: .tmp/capital_flows_chart_<date>.png)")
    args = parser.parse_args()

    # Default to --report if no output flag given
    show_report = args.report or args.all or not (args.table or args.chart)
    show_table  = args.table  or args.all
    show_chart  = args.chart  or args.all

    print(f"\nFetching OHLCV for {len(TICKERS)} tickers...")
    raw = fetch(list(TICKERS.keys()), start=args.start, end=args.end)
    if not raw:
        sys.exit("No data fetched.")

    print(f"\nComputing {WINDOWS}-day CMF...")
    wide = build_signal_stack(raw, windows=WINDOWS)

    today_str = datetime.today().strftime("%Y%m%d")
    out_path = args.out or str(
        Path(__file__).parent.parent / ".tmp" / f"capital_flows_{today_str}.csv"
    )
    save(wide, out_path)

    filtered = wide.dropna(how="all")
    if filtered.empty:
        sys.exit(f"Insufficient data — no complete CMF window in range. "
                 f"Try --start with an earlier date (need at least {max(WINDOWS)} trading days).")
    as_of = str(filtered.index[-1].date())
    snap = derive_snapshot(wide, raw, TICKERS, windows=WINDOWS)

    if show_report:
        print_watchlist(snap, as_of=as_of)

    if show_table:
        print_table(snap, as_of=as_of)

    if show_chart:
        chart_path = args.chart_out or str(
            Path(__file__).parent.parent / ".tmp" / f"capital_flows_chart_{today_str}.png"
        )
        render_heatmap(snap, as_of=as_of, out_path=chart_path)


if __name__ == "__main__":
    main()
