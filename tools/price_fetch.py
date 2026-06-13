"""
Price Data Fetcher + Realized Volatility
Fetches daily OHLC price data via yfinance and computes rolling realized volatility.

Usage examples:
  # Realized vol for multiple macro ETFs
  python tools/price_fetch.py --tickers SPY QQQ GLD USO XLE TLT --start 2010-01-01

  # Single ticker with custom window and output path
  python tools/price_fetch.py --tickers SPY --start 2000-01-01 --window 20 30 --out .tmp/spy_rv.csv

  # Current ATM implied vol snapshot from options chain
  python tools/price_fetch.py --tickers SPY TLT GLD --iv-snapshot

Requires: yfinance>=0.2.0  (pip install yfinance)
"""

import argparse
import os
import ssl
import sys
from datetime import datetime
from pathlib import Path

# Disable SSL cert verification for both Python urllib and curl_cffi (yfinance v1.2+)
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

# UTF-8 stdout for Windows cp1252 compatibility
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
from dotenv import load_dotenv

import yfinance as yf
from curl_cffi import requests as curl_requests

load_dotenv(Path(__file__).parent.parent / ".env")

YF_SESSION = curl_requests.Session(impersonate="chrome", verify=False)

ANNUALIZE = np.sqrt(252)
PARKINSON_CONST = 1.0 / (4.0 * np.log(2))  # ≈ 0.36067


def fetch(tickers: list[str], start: str, end: str | None) -> dict[str, pd.DataFrame]:
    """Download daily OHLC data for each ticker via yfinance (adjusted prices)."""
    result = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start, end=end, auto_adjust=True,
                             progress=False, session=YF_SESSION)
            if df is None or df.empty:
                print(f"  WARN: No data for {ticker}", file=sys.stderr)
                continue
            # yfinance may return MultiIndex columns when downloading a single ticker
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            print(f"  OK  {ticker:<6}  {len(df)} trading days  "
                  f"[{df.index[0].date()} to {df.index[-1].date()}]")
            result[ticker] = df
        except Exception as e:
            print(f"  FAIL {ticker}: {e}", file=sys.stderr)
    return result


def compute_rv(df: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
    """
    Compute realized volatility columns from OHLC daily data.

    Close-to-close:  rv  = std(log(C/C_prev), window) * sqrt(252) * 100
    Parkinson:       pk  = sqrt( PARKINSON_CONST * mean(log(H/L)^2) * 252 ) * 100
                         where PARKINSON_CONST = 1/(4*ln2) ≈ 0.3607

    Returns DataFrame with: close, rv_{w}d, pk_{w}d for each window w.
    """
    out = pd.DataFrame(index=df.index)
    out["close"] = df["Close"]

    log_returns = np.log(df["Close"] / df["Close"].shift(1))
    ln_hl_sq = np.log(df["High"] / df["Low"]) ** 2

    for w in windows:
        out[f"rv_{w}d"] = log_returns.rolling(w).std() * ANNUALIZE * 100
        out[f"pk_{w}d"] = (
            np.sqrt(PARKINSON_CONST * ln_hl_sq.rolling(w).mean() * 252) * 100
        )

    return out


def iv_snapshot(tickers: list[str]) -> pd.DataFrame:
    """
    Pull current ATM implied vol from each ticker's options chain (30-day target).
    Returns a DataFrame with columns: ticker, current_price, target_expiry, atm_strike, iv_pct.
    This is a point-in-time snapshot — not a historical series.
    """
    rows = []
    today = datetime.today().date()

    for ticker in tickers:
        try:
            t = yf.Ticker(ticker, session=YF_SESSION)
            expirations = t.options
            if not expirations:
                print(f"  WARN: No options data for {ticker}", file=sys.stderr)
                continue

            # Pick expiry closest to 30 calendar days out
            exp_dates = [datetime.strptime(e, "%Y-%m-%d").date() for e in expirations]
            target = min(exp_dates, key=lambda d: abs((d - today).days - 30))
            exp_str = target.strftime("%Y-%m-%d")

            chain = t.option_chain(exp_str)
            info = t.fast_info
            current_price = info.last_price

            # ATM call: strike closest to current price
            calls = chain.calls.copy()
            calls["dist"] = (calls["strike"] - current_price).abs()
            atm = calls.sort_values("dist").iloc[0]

            iv_pct = atm["impliedVolatility"] * 100  # yfinance returns as decimal

            rows.append({
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "target_expiry": exp_str,
                "days_to_expiry": (target - today).days,
                "atm_strike": atm["strike"],
                "iv_pct": round(iv_pct, 2),
            })
            print(f"  OK  {ticker:<6}  price={current_price:.2f}  "
                  f"expiry={exp_str} ({(target - today).days}d)  ATM IV={iv_pct:.1f}%")
        except Exception as e:
            print(f"  FAIL {ticker}: {e}", file=sys.stderr)

    return pd.DataFrame(rows)


def to_long(rv_dict: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Stack per-ticker DataFrames into long format with a 'ticker' column."""
    frames = []
    for ticker, df_rv in rv_dict.items():
        df_rv = df_rv.copy()
        df_rv.insert(0, "ticker", ticker)
        frames.append(df_rv)
    combined = pd.concat(frames)
    combined.index.name = "date"
    return combined.sort_index()


def save(df: pd.DataFrame, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path)
    print(f"\nSaved {df.shape[0]} rows x {df.shape[1]} cols -> {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch price data and compute realized volatility"
    )
    parser.add_argument("--tickers", nargs="+", required=True,
                        help="Ticker symbols (e.g. SPY QQQ GLD USO XLE TLT)")
    parser.add_argument("--start", default="2000-01-01",
                        help="Start date YYYY-MM-DD (default: 2000-01-01)")
    parser.add_argument("--end", default=None,
                        help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--window", nargs="+", type=int, default=[20, 30],
                        help="Rolling window(s) in trading days (default: 20 30)")
    parser.add_argument("--out", default=None,
                        help="Output CSV path (default: .tmp/prices_<tickers>_<date>.csv)")
    parser.add_argument("--iv-snapshot", action="store_true",
                        help="Pull current ATM implied vol from options chain (snapshot only)")
    args = parser.parse_args()

    if args.iv_snapshot:
        print(f"\nFetching IV snapshot for: {', '.join(args.tickers)}")
        snap = iv_snapshot(args.tickers)
        if snap.empty:
            sys.exit("No IV data retrieved.")
        today = datetime.today().strftime("%Y%m%d")
        out_path = args.out or str(
            Path(__file__).parent.parent / ".tmp" / f"iv_snapshot_{today}.csv"
        )
        save(snap, out_path)
        print(snap.to_string(index=False))
        return

    print(f"\nFetching OHLC data for: {', '.join(args.tickers)}")
    raw = fetch(args.tickers, start=args.start, end=args.end)

    if not raw:
        sys.exit("No data fetched — check ticker symbols and date range.")

    rv_data = {}
    for ticker, ohlc in raw.items():
        rv_data[ticker] = compute_rv(ohlc, windows=args.window)

    out_df = to_long(rv_data)

    if args.out is None:
        today = datetime.today().strftime("%Y%m%d")
        slug = "_".join(args.tickers[:3])
        args.out = str(
            Path(__file__).parent.parent / ".tmp" / f"prices_{slug}_{today}.csv"
        )

    save(out_df, args.out)

    first = args.tickers[0]
    sample = out_df[out_df["ticker"] == first].tail(5)
    print(f"\nSample ({first}, last 5 rows):")
    print(sample.to_string())


if __name__ == "__main__":
    main()
