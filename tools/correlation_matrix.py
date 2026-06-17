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
import matplotlib.pyplot as plt
import seaborn as sns

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


def plot_three_panel(
    current: pd.DataFrame,
    prior: pd.DataFrame,
    delta: pd.DataFrame,
    labels: dict[str, str],
    current_label: str,
    prior_label: str,
    out_path: str,
) -> None:
    """Render a 3-panel (current / prior / delta) correlation heatmap and save to PNG."""
    def relabel(df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(index=labels, columns=labels)

    cur = relabel(current)
    pri = relabel(prior)
    dlt = relabel(delta)

    n = len(cur)
    diag_mask = np.eye(n, dtype=bool)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor("white")

    kw_base = dict(
        annot=True,
        linewidths=0.5,
        linecolor="#e5e5e5",
        cbar=True,
        square=True,
        annot_kws={"size": 9},
    )

    # Panel 1 — Current
    sns.heatmap(cur, ax=axes[0], mask=diag_mask,
                cmap="RdBu_r", vmin=-1, vmax=1, fmt=".2f",
                cbar_kws={"shrink": 0.8}, **kw_base)
    axes[0].set_title(f"Current\n{current_label}", fontsize=11, fontweight="bold")

    # Panel 2 — Prior (1 week)
    sns.heatmap(pri, ax=axes[1], mask=diag_mask,
                cmap="RdBu_r", vmin=-1, vmax=1, fmt=".2f",
                cbar_kws={"shrink": 0.8}, **kw_base)
    axes[1].set_title(f"Prior (1 week)\n{prior_label}", fontsize=11, fontweight="bold")

    # Panel 3 — Delta
    sns.heatmap(dlt, ax=axes[2], mask=diag_mask,
                cmap="RdYlGn", vmin=-0.5, vmax=0.5, fmt="+.2f",
                cbar_kws={"shrink": 0.8}, **kw_base)
    axes[2].set_title("Delta (Current − Prior)", fontsize=11, fontweight="bold")

    fig.suptitle(
        f"63-Day Correlation Snapshot  |  Current: {current_label}  vs  Prior: {prior_label}",
        fontsize=13, fontweight="bold", y=1.02,
    )
    fig.text(0.5, -0.02,
             "Source: Yahoo Finance via yfinance  |  DeltaTheta",
             ha="center", fontsize=8, color="#6B7280")

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"\nChart saved -> {out_path}")
