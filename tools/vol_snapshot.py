"""
Volatility Snapshot Table
Pulls current implied vol (CBOE indices via FRED + options chains via yfinance)
and trailing realized vol for major macro ETFs, then renders a color-shaded
comparison table as a publication-ready PNG.

IV sources:
  SPY  → CBOE VIX  (VIXCLS via FRED)
  QQQ  → CBOE VXN  (VXNCLS via FRED)
  GLD  → CBOE GVZ  (GVZCLS via FRED)
  USO  → CBOE OVX  (VXOCLS via FRED)
  XLE  → ATM options chain (yfinance snapshot)
  TLT  → ATM options chain (yfinance snapshot)

Usage:
  python tools/vol_snapshot.py
  python tools/vol_snapshot.py --out-png .tmp/vol_table.png --out-csv .tmp/vol_snapshot.csv
  python tools/vol_snapshot.py --rv-window 20   # override realized vol lookback
"""

import argparse
import os
import ssl
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Disable SSL cert verification for both Python urllib (FRED) and curl_cffi (yfinance v1.2+)
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

# UTF-8 stdout so Unicode characters (minus signs, etc.) don't crash on Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

import yfinance as yf
from curl_cffi import requests as curl_requests

# yfinance 1.2+ uses curl_cffi internally; inject a no-verify session so
# it works on Windows machines without a properly configured CA bundle.
YF_SESSION = curl_requests.Session(impersonate="chrome", verify=False)

load_dotenv(Path(__file__).parent.parent / ".env")

# ── Ticker configuration ──────────────────────────────────────────────────────

TICKERS = [
    {"ticker": "SPY", "asset": "S&P 500",        "iv_series": "VIXCLS",  "iv_source": "CBOE VIX"},
    {"ticker": "QQQ", "asset": "NASDAQ-100",      "iv_series": "VXNCLS",  "iv_source": "CBOE VXN"},
    {"ticker": "GLD", "asset": "Gold",             "iv_series": "GVZCLS",  "iv_source": "CBOE GVZ"},
    # USO used for implied vol (liquid options, best free proxy after OVX/VXOCLS was
    # discontinued Sept 2021). Realized vol uses CL=F (WTI continuous front-month
    # futures) to avoid USO's ETF roll drag — in contango the monthly roll creates
    # a small but real negative yield that inflates long-run returns vs. spot crude.
    # The RV/IV split is documented in the IV Source column of the output table.
    {"ticker": "USO", "asset": "Crude Oil (WTI)", "iv_series": None,
     "iv_source": "USO opts / CL=F RV", "rv_ticker": "CL=F"},
    {"ticker": "XLE", "asset": "Energy (Sector)",  "iv_series": None,       "iv_source": "Options chain"},
    {"ticker": "TLT", "asset": "Long Treasury",    "iv_series": None,       "iv_source": "Options chain"},
]

PARKINSON_CONST = 1.0 / (4.0 * np.log(2))  # ≈ 0.36067


# ── Data fetching ─────────────────────────────────────────────────────────────

def fetch_cboe_iv(series_ids: list[str]) -> dict[str, tuple[float, str]]:
    """
    Fetch the most recent daily value for each CBOE vol index from FRED.
    Returns dict: series_id -> (value, date_str).
    """
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "your_fred_api_key_here":
        sys.exit("ERROR: FRED_API_KEY not set in .env")

    fred = Fred(api_key=api_key)
    result = {}
    start = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    for sid in series_ids:
        try:
            s = fred.get_series(sid, observation_start=start)
            s = s.dropna()
            if s.empty:
                print(f"  WARN: No recent data for {sid}", file=sys.stderr)
                continue
            latest_val = float(s.iloc[-1])
            latest_date = s.index[-1].strftime("%Y-%m-%d")
            result[sid] = (latest_val, latest_date)
            print(f"  OK  {sid:<10} {latest_val:.2f}%  (as of {latest_date})")
        except Exception as e:
            print(f"  FAIL {sid}: {e}", file=sys.stderr)

    return result


def fetch_options_iv(ticker: str) -> tuple[float | None, str | None]:
    """
    Fetch ATM ~30-day implied vol from yfinance options chain.
    Returns (iv_pct, expiry_str) or (None, None) on failure.
    """
    today = datetime.today().date()
    try:
        t = yf.Ticker(ticker, session=YF_SESSION)
        expirations = t.options
        if not expirations:
            print(f"  WARN: No options for {ticker}", file=sys.stderr)
            return None, None

        exp_dates = [datetime.strptime(e, "%Y-%m-%d").date() for e in expirations]
        target = min(exp_dates, key=lambda d: abs((d - today).days - 30))
        exp_str = target.strftime("%Y-%m-%d")

        chain = t.option_chain(exp_str)
        current_price = t.fast_info.last_price

        calls = chain.calls.copy()
        calls["dist"] = (calls["strike"] - current_price).abs()
        atm = calls.sort_values("dist").iloc[0]
        iv_pct = atm["impliedVolatility"] * 100

        print(f"  OK  {ticker:<10} {iv_pct:.2f}%  (ATM options, exp {exp_str})")
        return iv_pct, exp_str

    except Exception as e:
        print(f"  FAIL {ticker} options: {e}", file=sys.stderr)
        return None, None


def fetch_rv(tickers: list[str], window: int) -> dict[str, float | None]:
    """
    Fetch recent OHLC for each ticker and compute Parkinson realized vol
    over the last `window` trading days. Returns dict: ticker -> rv_pct.
    """
    # Pull enough history for the rolling window + buffer
    start = (datetime.today() - timedelta(days=window * 2 + 30)).strftime("%Y-%m-%d")
    result = {}

    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start, auto_adjust=True,
                             progress=False, session=YF_SESSION)
            if df is None or df.empty:
                result[ticker] = None
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            ln_hl_sq = np.log(df["High"] / df["Low"]) ** 2

            # Roll-gap filter for continuous futures (e.g. CL=F, BZ=F).
            # When the front-month contract expires (~monthly), Yahoo stitches to
            # the next contract. The day-of-roll can show a High/Low spread that
            # reflects the price *difference between contracts*, not an actual
            # intraday move. Capping at ln(H/L) > 0.10 (≈ H/L > 1.105, ~10% range)
            # suppresses these outliers without touching normal trading-day variance.
            if ticker.endswith("=F"):
                roll_mask = np.log(df["High"] / df["Low"]) > 0.10
                if roll_mask.any():
                    print(f"  NOTE {ticker:<10} {roll_mask.sum()} roll-gap day(s) filtered")
                ln_hl_sq = ln_hl_sq.where(~roll_mask)

            pk = np.sqrt(PARKINSON_CONST * ln_hl_sq.tail(window).mean() * 252) * 100
            result[ticker] = round(float(pk), 2)
            print(f"  OK  {ticker:<10} RV (Parkinson {window}d) = {pk:.2f}%")
        except Exception as e:
            print(f"  FAIL {ticker} RV: {e}", file=sys.stderr)
            result[ticker] = None

    return result


# ── Table assembly ────────────────────────────────────────────────────────────

def build_table(cboe_iv: dict, rv_data: dict, window: int) -> pd.DataFrame:
    """Assemble the VRP comparison DataFrame with display formatting."""
    rows = []
    for cfg in TICKERS:
        ticker = cfg["ticker"]
        iv_val = None
        iv_date = "—"

        if cfg["iv_series"] and cfg["iv_series"] in cboe_iv:
            iv_val, iv_date = cboe_iv[cfg["iv_series"]]
        elif cfg["iv_series"] is None:
            # Fetched separately via options chain (stored in cboe_iv under ticker key)
            opt_key = f"OPT_{ticker}"
            if opt_key in cboe_iv:
                iv_val, iv_date = cboe_iv[opt_key]

        rv_val = rv_data.get(ticker)
        vrp = round(iv_val - rv_val, 2) if (iv_val is not None and rv_val is not None) else None

        def fmt(v):
            return f"{v:.1f}%" if v is not None else "N/A"

        def fmt_vrp(v):
            if v is None:
                return "N/A"
            sign = "+" if v >= 0 else "-"
            return f"{sign}{abs(v):.1f}%"

        rows.append({
            "Ticker":          ticker,
            "Asset":           cfg["asset"],
            "IV Source":       cfg["iv_source"],
            "Current IV":      fmt(iv_val),
            f"RV {window}d (Parkinson)": fmt(rv_val),
            "VRP (IV − RV)":  fmt_vrp(vrp),
            "IV Date":         iv_date,
            # Raw numerics for coloring (not displayed)
            "_iv_raw":  iv_val,
            "_rv_raw":  rv_val,
            "_vrp_raw": vrp,
        })

    return pd.DataFrame(rows)


# ── Rendering ─────────────────────────────────────────────────────────────────

def render_table(df: pd.DataFrame, output_path: str, window: int) -> None:
    """Render the VRP table as a color-shaded PNG."""

    DISPLAY_COLS = [
        "Ticker", "Asset", "IV Source",
        "Current IV", f"RV {window}d (Parkinson)", "VRP (IV − RV)", "IV Date"
    ]
    df_show = df[DISPLAY_COLS]
    vrp_raw = df["_vrp_raw"].values

    n_rows = len(df_show)
    n_cols = len(DISPLAY_COLS)

    # Dynamic sizing
    fig_w = 13
    row_h = 0.52
    header_h = 0.65
    title_space = 0.9
    fig_h = title_space + header_h + n_rows * row_h + 0.5

    fig = plt.figure(figsize=(fig_w, fig_h), facecolor="white")
    ax = fig.add_subplot(111)
    ax.axis("off")

    today_str = datetime.today().strftime("%B %d, %Y")
    fig.text(0.5, 0.97, "Volatility Snapshot: Implied vs. Realized",
             ha="center", va="top", fontsize=14, fontweight="bold", color="#1a1a2e")
    fig.text(0.5, 0.91,
             f"As of {today_str}  ·  IV: CBOE indices (FRED) + options chain (yfinance)  ·  RV: Parkinson estimator ({window}d)",
             ha="center", va="top", fontsize=8.5, color="#666666", style="italic")

    # Build table
    cell_text = [list(row) for row in df_show.itertuples(index=False)]
    table = ax.table(
        cellText=cell_text,
        colLabels=DISPLAY_COLS,
        cellLoc="center",
        loc="center",
        bbox=[0, 0, 1, 0.82],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10.5)

    # Column widths (sum to ~1)
    col_widths = [0.08, 0.16, 0.14, 0.12, 0.17, 0.14, 0.11]
    for ci, w in enumerate(col_widths):
        for ri in range(n_rows + 1):
            table[ri, ci].set_width(w)

    # Header row
    HEADER_BG = "#1a1a2e"
    for ci in range(n_cols):
        cell = table[0, ci]
        cell.set_facecolor(HEADER_BG)
        cell.set_text_props(color="white", fontweight="bold", fontsize=10)
        cell.set_height(header_h / (fig_h - title_space) * 0.82)
        cell.set_edgecolor("#ffffff")

    # Data rows
    vrp_col_idx = DISPLAY_COLS.index("VRP (IV − RV)")
    norm = mcolors.TwoSlopeNorm(vmin=-10, vcenter=0, vmax=15)
    cmap = plt.cm.RdYlGn

    ROW_ALT = ["#f0f4f8", "#ffffff"]
    for ri in range(n_rows):
        row_bg = ROW_ALT[ri % 2]
        for ci in range(n_cols):
            cell = table[ri + 1, ci]
            cell.set_edgecolor("#d0d7de")
            cell.set_height(row_h / (fig_h - title_space) * 0.82)

            if ci == vrp_col_idx and vrp_raw[ri] is not None and not np.isnan(vrp_raw[ri]):
                r, g, b, _ = cmap(norm(vrp_raw[ri]))
                cell.set_facecolor((r, g, b, 0.7))
                # Bold the VRP cell text
                cell.set_text_props(fontweight="bold")
            else:
                cell.set_facecolor(row_bg)

    # Ticker column — slightly bolder
    for ri in range(n_rows):
        table[ri + 1, 0].set_text_props(fontweight="bold")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none", pad_inches=0.25)
    plt.close()
    print(f"\nTable saved -> {output_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate volatility snapshot table")
    parser.add_argument("--rv-window", type=int, default=20,
                        help="Realized vol rolling window in trading days (default: 20)")
    parser.add_argument("--out-png", default=None,
                        help="Output PNG path (default: .tmp/vol_snapshot_<date>.png)")
    parser.add_argument("--out-csv", default=None,
                        help="Output CSV path (default: .tmp/vol_snapshot_<date>.csv)")
    args = parser.parse_args()

    today = datetime.today().strftime("%Y%m%d")
    root = Path(__file__).parent.parent
    png_path = args.out_png or str(root / ".tmp" / f"vol_snapshot_{today}.png")
    csv_path = args.out_csv or str(root / ".tmp" / f"vol_snapshot_{today}.csv")

    # ── 1. Implied vol: CBOE series via FRED ─────────────────────────────────
    cboe_series = [cfg["iv_series"] for cfg in TICKERS if cfg["iv_series"] is not None]
    print(f"\nFetching CBOE implied vol from FRED ({len(cboe_series)} series)...")
    cboe_iv = fetch_cboe_iv(cboe_series)

    # ── 2. Implied vol: options chain for tickers without a CBOE index ───────
    options_tickers = [cfg["ticker"] for cfg in TICKERS if cfg["iv_series"] is None]
    if options_tickers:
        print(f"\nFetching options chain IV for: {', '.join(options_tickers)}...")
        for ticker in options_tickers:
            iv_val, iv_date = fetch_options_iv(ticker)
            if iv_val is not None:
                cboe_iv[f"OPT_{ticker}"] = (iv_val, iv_date)

    # ── 3. Realized vol via yfinance OHLC ────────────────────────────────────
    # Use rv_ticker when specified (e.g. CL=F for crude instead of USO).
    # fetch_rv keys results by the ticker it was passed; remap to display ticker.
    rv_tickers = [cfg.get("rv_ticker", cfg["ticker"]) for cfg in TICKERS]
    print(f"\nFetching realized vol (Parkinson {args.rv_window}d) via yfinance...")
    rv_raw = fetch_rv(rv_tickers, window=args.rv_window)

    # Remap: { rv_ticker -> value }  →  { display_ticker -> value }
    rv_data = {}
    for cfg in TICKERS:
        rv_key = cfg.get("rv_ticker", cfg["ticker"])
        rv_data[cfg["ticker"]] = rv_raw.get(rv_key)

    # ── 4. Assemble table ────────────────────────────────────────────────────
    print("\nAssembling table...")
    df = build_table(cboe_iv, rv_data, window=args.rv_window)

    # Save CSV (display columns + raw numerics)
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"CSV saved  -> {csv_path}")

    # ── 5. Render colored table PNG ──────────────────────────────────────────
    print("\nRendering table PNG...")
    render_table(df, png_path, window=args.rv_window)

    # Print to console
    display_cols = [c for c in df.columns if not c.startswith("_")]
    print()
    print(df[display_cols].to_string(index=False))


if __name__ == "__main__":
    main()
