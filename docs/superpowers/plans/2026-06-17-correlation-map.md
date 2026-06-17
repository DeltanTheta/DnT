# Correlation Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a generic, reusable `tools/correlation_matrix.py` that generates a 3-panel correlation heatmap (current 63d / prior 63d / delta) for a configurable set of macro asset proxy tickers, then write Substack post #12 around the live output.

**Architecture:** Standalone script following the same pattern as `tools/price_fetch.py` — yfinance for data, curl_cffi session, argparse CLI, matplotlib/seaborn for output. Pure computation functions (`compute_log_returns`, `correlation_window`) are tested with synthetic data. Visualization and CLI are integration-tested by running against live data and inspecting output.

**Tech Stack:** Python 3.11+, yfinance, curl_cffi, pandas, numpy, matplotlib, seaborn, python-dotenv

---

## Task 1: Scaffold core computation functions + tests

**Files:**
- Create: `tools/correlation_matrix.py` (computation functions only — no CLI, no viz yet)
- Create: `tests/test_correlation_matrix.py`

- [ ] **Step 1: Install seaborn if not present**

```bash
pip install seaborn
```

Expected: `Successfully installed seaborn-X.X.X` or `already satisfied`.

- [ ] **Step 2: Write the failing tests**

Create `tests/test_correlation_matrix.py`:

```python
import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools.correlation_matrix import compute_log_returns, correlation_window


def make_prices(n=150, tickers=("A", "B", "C"), seed=42):
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((n, len(tickers))).cumsum(axis=0) + 100
    idx = pd.bdate_range("2024-01-01", periods=n)
    return pd.DataFrame(data, index=idx, columns=list(tickers))


def test_log_returns_drops_first_row():
    prices = make_prices(100)
    returns = compute_log_returns(prices)
    assert returns.shape == (99, 3)


def test_log_returns_correct_value():
    prices = pd.DataFrame(
        {"A": [100.0, 110.0, 99.0]},
        index=pd.bdate_range("2024-01-01", periods=3),
    )
    returns = compute_log_returns(prices)
    assert len(returns) == 2
    assert abs(returns["A"].iloc[0] - np.log(110.0 / 100.0)) < 1e-10
    assert abs(returns["A"].iloc[1] - np.log(99.0 / 110.0)) < 1e-10


def test_correlation_window_shape_and_diagonal():
    prices = make_prices(150)
    returns = compute_log_returns(prices)
    corr = correlation_window(returns, end_offset=0, window=63)
    assert corr.shape == (3, 3)
    for col in corr.columns:
        assert abs(corr.loc[col, col] - 1.0) < 1e-10


def test_correlation_window_current_vs_prior_differ():
    prices = make_prices(150)
    returns = compute_log_returns(prices)
    cur = correlation_window(returns, end_offset=0, window=63)
    pri = correlation_window(returns, end_offset=5, window=63)
    assert not cur.equals(pri)


def test_correlation_window_prior_slice_is_correct():
    prices = make_prices(150)
    returns = compute_log_returns(prices)
    prior = correlation_window(returns, end_offset=5, window=63)
    expected = returns.iloc[-(63 + 5):-5].corr()
    pd.testing.assert_frame_equal(prior, expected)


def test_correlation_window_current_slice_is_correct():
    prices = make_prices(150)
    returns = compute_log_returns(prices)
    current = correlation_window(returns, end_offset=0, window=63)
    expected = returns.iloc[-63:].corr()
    pd.testing.assert_frame_equal(current, expected)
```

- [ ] **Step 3: Run tests to verify they all fail**

```bash
cd e:/DnT && python -m pytest tests/test_correlation_matrix.py -v
```

Expected: `ModuleNotFoundError: No module named 'tools.correlation_matrix'` or similar — all tests fail because the module doesn't exist yet.

- [ ] **Step 4: Create `tools/correlation_matrix.py` with computation functions only**

```python
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

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
ssl._create_default_https_context = ssl._create_unverified_context

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


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
```

- [ ] **Step 5: Run tests to verify they all pass**

```bash
cd e:/DnT && python -m pytest tests/test_correlation_matrix.py -v
```

Expected output:
```
tests/test_correlation_matrix.py::test_log_returns_drops_first_row PASSED
tests/test_correlation_matrix.py::test_log_returns_correct_value PASSED
tests/test_correlation_matrix.py::test_correlation_window_shape_and_diagonal PASSED
tests/test_correlation_matrix.py::test_correlation_window_current_vs_prior_differ PASSED
tests/test_correlation_matrix.py::test_correlation_window_prior_slice_is_correct PASSED
tests/test_correlation_matrix.py::test_correlation_window_current_slice_is_correct PASSED
6 passed in 0.Xs
```

- [ ] **Step 6: Commit**

```bash
cd e:/DnT && git add tools/correlation_matrix.py tests/test_correlation_matrix.py
git commit -m "feat: add correlation_matrix core computation functions + tests"
```

---

## Task 2: Add price fetch and top-movers printer

**Files:**
- Modify: `tools/correlation_matrix.py` — add `fetch_closes` and `print_top_movers`

- [ ] **Step 1: Add `fetch_closes` and `print_top_movers` to `tools/correlation_matrix.py`**

Add these imports at the top of the file (after the existing imports):

```python
from dotenv import load_dotenv
import yfinance as yf
from curl_cffi import requests as curl_requests

load_dotenv(Path(__file__).parent.parent / ".env")

YF_SESSION = curl_requests.Session(impersonate="chrome", verify=False)
```

Add these functions after `correlation_window`:

```python
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
    delta = current - prior
    tickers = list(current.columns)
    pairs = []
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            a, b = tickers[i], tickers[j]
            d = delta.loc[a, b]
            c = current.loc[a, b]
            p = prior.loc[a, b]
            pairs.append((abs(d), a, b, p, c, d))
    pairs.sort(reverse=True)
    print(f"\nTop {n} movers (prior → current):")
    for _, a, b, p, c, d in pairs[:n]:
        sign = "+" if d >= 0 else ""
        print(f"  {a} / {b:<14}  {p:+.2f} → {c:+.2f}  ({sign}{d:.2f})")
```

- [ ] **Step 2: Verify existing tests still pass**

```bash
cd e:/DnT && python -m pytest tests/test_correlation_matrix.py -v
```

Expected: 6 passed.

- [ ] **Step 3: Commit**

```bash
cd e:/DnT && git add tools/correlation_matrix.py
git commit -m "feat: add fetch_closes and print_top_movers to correlation_matrix"
```

---

## Task 3: Add 3-panel heatmap visualization

**Files:**
- Modify: `tools/correlation_matrix.py` — add `plot_three_panel`

- [ ] **Step 1: Add `plot_three_panel` to `tools/correlation_matrix.py`**

Add these imports at the top (after existing imports):

```python
import matplotlib.pyplot as plt
import seaborn as sns
```

Add this function after `print_top_movers`:

```python
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
```

- [ ] **Step 2: Verify tests still pass**

```bash
cd e:/DnT && python -m pytest tests/test_correlation_matrix.py -v
```

Expected: 6 passed.

- [ ] **Step 3: Commit**

```bash
cd e:/DnT && git add tools/correlation_matrix.py
git commit -m "feat: add 3-panel heatmap visualization to correlation_matrix"
```

---

## Task 4: Wire CLI (argparse) and `main()`

**Files:**
- Modify: `tools/correlation_matrix.py` — add `main()` and `if __name__ == "__main__"` block

- [ ] **Step 1: Add `main()` to the end of `tools/correlation_matrix.py`**

```python
def main() -> None:
    import argparse
    from datetime import datetime, timedelta

    parser = argparse.ArgumentParser(
        description="Compute and visualize macro asset correlation matrix (current vs prior)"
    )
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS,
                        help="Ticker symbols (default: SPY IWM QQQ TLT IEF GLD DX-Y.NYB)")
    parser.add_argument("--window", type=int, default=63,
                        help="Lookback window in trading days (default: 63)")
    parser.add_argument("--prior-offset", type=int, default=5, dest="prior_offset",
                        help="Trading days to shift the prior window back (default: 5 = 1 week)")
    parser.add_argument("--lookback-days", type=int, default=400, dest="lookback_days",
                        help="Calendar days of price history to fetch (default: 400)")
    parser.add_argument("--start", default=None,
                        help="Override start date YYYY-MM-DD (ignores --lookback-days)")
    parser.add_argument("--end", default=None,
                        help="Override end date YYYY-MM-DD (default: today)")
    parser.add_argument("--labels", nargs="+", default=[],
                        help="Display name overrides: TICKER:LABEL pairs e.g. DX-Y.NYB:DXY")
    parser.add_argument("--out", default=None,
                        help="Output PNG path (default: .tmp/correlation_matrix_YYYYMMDD.png)")
    args = parser.parse_args()

    end_date = args.end or datetime.today().strftime("%Y-%m-%d")
    if args.start:
        start_date = args.start
    else:
        start_date = (
            datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=args.lookback_days)
        ).strftime("%Y-%m-%d")

    label_map = dict(DEFAULT_LABELS)
    for pair in args.labels:
        if ":" in pair:
            ticker, label = pair.split(":", 1)
            label_map[ticker] = label

    print(f"\nFetching prices: {', '.join(args.tickers)}")
    print(f"  Date range: {start_date} to {end_date}\n")

    prices = fetch_closes(args.tickers, start=start_date, end=end_date)
    if prices.empty:
        sys.exit("No price data fetched — check tickers and network.")

    returns = compute_log_returns(prices)
    min_needed = args.window + args.prior_offset
    if len(returns) < min_needed:
        sys.exit(
            f"Not enough data: need {min_needed} trading-day rows, got {len(returns)}. "
            f"Increase --lookback-days."
        )

    current_corr = correlation_window(returns, end_offset=0, window=args.window)
    prior_corr   = correlation_window(returns, end_offset=args.prior_offset, window=args.window)
    delta_corr   = current_corr - prior_corr

    def window_label(end_offset: int) -> str:
        if end_offset == 0:
            sl = returns.iloc[-args.window:]
        else:
            sl = returns.iloc[-(args.window + end_offset):-end_offset]
        return f"{sl.index[0].strftime('%b %d')} – {sl.index[-1].strftime('%b %d, %Y')}"

    current_label = window_label(0)
    prior_label   = window_label(args.prior_offset)

    print_top_movers(current_corr, prior_corr)

    today_str = datetime.today().strftime("%Y%m%d")
    out_path = args.out or str(
        Path(__file__).parent.parent / ".tmp" / f"correlation_matrix_{today_str}.png"
    )

    plot_three_panel(
        current=current_corr,
        prior=prior_corr,
        delta=delta_corr,
        labels=label_map,
        current_label=current_label,
        prior_label=prior_label,
        out_path=out_path,
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify tests still pass**

```bash
cd e:/DnT && python -m pytest tests/test_correlation_matrix.py -v
```

Expected: 6 passed.

- [ ] **Step 3: Commit**

```bash
cd e:/DnT && git add tools/correlation_matrix.py
git commit -m "feat: add CLI main() to correlation_matrix — script is now runnable"
```

---

## Task 5: Run end-to-end against live data

**Files:**
- No code changes — this is a live verification step
- Output: `.tmp/correlation_matrix_<YYYYMMDD>.png` (needed for post)

- [ ] **Step 1: Run the script with default tickers**

```bash
cd e:/DnT && python tools/correlation_matrix.py
```

Expected output (exact values will differ by run date):
```
Fetching prices: SPY, IWM, QQQ, TLT, IEF, GLD, DX-Y.NYB
  Date range: 2025-05-13 to 2026-06-17

  OK  SPY           275 trading days  [2025-05-13 to 2026-06-17]
  OK  IWM           275 trading days  [2025-05-13 to 2026-06-17]
  OK  QQQ           275 trading days  [2025-05-13 to 2026-06-17]
  OK  TLT           275 trading days  [2025-05-13 to 2026-06-17]
  OK  IEF           275 trading days  [2025-05-13 to 2026-06-17]
  OK  GLD           275 trading days  [2025-05-13 to 2026-06-17]
  OK  DX-Y.NYB      275 trading days  [2025-05-13 to 2026-06-17]

Top 5 movers (prior → current):
  SPY / TLT         +X.XX → +X.XX  (+X.XX)
  ...

Chart saved -> .tmp/correlation_matrix_20260617.png
```

- [ ] **Step 2: Open the PNG and verify all three panels render correctly**

Open `.tmp/correlation_matrix_<date>.png`. Check:
- All 7 tickers appear on both axes of each panel (DX-Y.NYB shows as "DXY")
- Panel 1 and Panel 2 use the blue-red diverging scale (-1 to +1)
- Panel 3 uses the green-yellow-red scale (-0.5 to +0.5) with `+/-` annotated values
- Diagonal cells are white/masked in all three panels
- Figure title shows both date windows correctly

If DXY does not appear (yfinance sometimes has gaps in `DX-Y.NYB`), re-run with `--tickers SPY IWM QQQ TLT IEF GLD` and note the gap in the post.

- [ ] **Step 3: Record the top-movers output**

Copy the "Top 5 movers" block from the terminal — you'll use the specific pairs and values when writing the post in Task 7.

- [ ] **Step 4: Commit the PNG to `.tmp/` is intentionally skipped**

`.tmp/` is gitignored by convention (regenerated on demand). No commit needed here.

---

## Task 6: Write the workflow SOP

**Files:**
- Create: `workflows/correlation_matrix.md`

- [ ] **Step 1: Create `workflows/correlation_matrix.md`**

```markdown
# Workflow: Correlation Matrix

## Objective

Generate a 3-panel correlation heatmap for a configurable set of macro asset proxy
tickers: current 63-day snapshot, 1-week-prior snapshot, and the delta between them.
Used to identify shifting inter-asset relationships across macro regimes.

## When to Run

- Publishing a correlation-focused post
- Monitoring regime changes (run weekly or after major macro events)
- Adding/removing tickers to explore a new factor relationship

## Prerequisites

```sh
pip install seaborn yfinance curl_cffi pandas numpy matplotlib python-dotenv
```

No API keys required — data comes from Yahoo Finance via yfinance (free).

## Execution

**Default run (7 tickers, 63-day window, 1-week prior):**

```sh
python tools/correlation_matrix.py
```

**Custom tickers:**

```sh
python tools/correlation_matrix.py --tickers SPY TLT GLD USO XLE
```

**Custom window (21-day = ~1 month):**

```sh
python tools/correlation_matrix.py --window 21
```

**Custom prior offset (compare to 1 month ago instead of 1 week):**

```sh
python tools/correlation_matrix.py --prior-offset 21
```

**Override display labels:**

```sh
python tools/correlation_matrix.py --labels DX-Y.NYB:DXY IEF:10Y
```

**Save to a specific path:**

```sh
python tools/correlation_matrix.py --out .tmp/corr_custom.png
```

## Default Ticker Set

| Ticker | Yahoo Symbol | Macro Factor |
|--------|-------------|--------------|
| SPY | SPY | US equities (S&P 500) |
| IWM | IWM | Risk appetite / small caps (Russell 2000) |
| QQQ | QQQ | Growth / tech (Nasdaq 100) |
| TLT | TLT | Long-duration rates (20Y+ Treasuries) |
| IEF | IEF | 10Y note proxy (7–10Y Treasuries) |
| GLD | GLD | Gold / real assets / fear |
| DXY | DX-Y.NYB | US dollar strength |

## Adding or Removing Tickers

Pass `--tickers` with the new set. No code changes needed.

```sh
# Add crude oil and remove IWM
python tools/correlation_matrix.py --tickers SPY QQQ TLT IEF GLD DX-Y.NYB USO
```

If a ticker's display name is ugly (e.g. `DX-Y.NYB`), add it to `DEFAULT_LABELS`
in the script or pass `--labels DX-Y.NYB:DXY` at call time.

## How to Interpret the Delta Panel

The delta heatmap (Panel 3) shows `current_corr - prior_corr` for each pair:

- **Green cell (+):** The two assets became more positively correlated this week.
  If SPY/TLT goes green, equities and bonds are moving more together — risk-off
  diversification is weakening.
- **Red cell (-):** Correlation fell. Assets are moving more independently or
  more inversely.
- **Near zero (yellow):** Relationship is stable week-over-week.

The magnitude matters: a delta of ±0.10 is noise; ±0.25+ is worth noting.

## Known Quirks

- **DX-Y.NYB (DXY):** Yahoo Finance's DXY index can have missing sessions
  on days when US markets are open. If it causes errors, substitute `UUP`
  (Invesco USD Bull ETF) which has fewer gaps, or just drop it from `--tickers`.
- **SSL:** `CURL_CA_BUNDLE` and `REQUESTS_CA_BUNDLE` are cleared at import time
  (same workaround as all other tools in this project — required for yfinance on
  some Windows environments).
- **Market holidays:** yfinance returns only trading days, so `--window 63`
  is truly 63 trading days regardless of calendar gaps.

## Output

PNG saved to `.tmp/correlation_matrix_YYYYMMDD.png`.
`.tmp/` is gitignored — regenerate on demand.
```

- [ ] **Step 2: Commit**

```bash
cd e:/DnT && git add workflows/correlation_matrix.md
git commit -m "docs: add correlation_matrix workflow SOP"
```

---

## Task 7: Write the post draft

**Files:**
- Create: `drafts/post_12_correlation_map.md`

> **Prerequisite:** Task 5 must be complete. You need the live top-movers output
> and the PNG in `.tmp/` before writing this task.

- [ ] **Step 1: Re-run the script to get the freshest data for the post**

```bash
cd e:/DnT && python tools/correlation_matrix.py
```

Note the following from the terminal output for use in the post body:
- The two date windows shown in the top-movers section
- The top 3 pairs by absolute delta and their direction (+ or -)
- Any pair with a delta > 0.15 — these are the ones worth calling out

- [ ] **Step 2: Create `drafts/post_12_correlation_map.md`**

Use this template, filling in the bracketed placeholders with actual values from Step 1:

```markdown
# The Correlation Map: How Macro Assets Are Moving Together Right Now

*DeltaTheta | Post 12 of the Build Series*

*Written by Claude with oversight.*

Most macro analysis focuses on individual assets: where is the 10-year yield
headed, is gold breaking out, will the dollar weaken. But the relationships
*between* assets often carry more signal than any single price level. A flight
to safety only works if bonds and equities are actually moving in opposite
directions. A risk-on rally has a different character when small caps and tech
are correlated at 0.95 versus when they're diverging. Correlations are the
structure the market is trading *through*, and that structure changes.

This post introduces a new tool in the pipeline that measures those correlations
across seven macro asset proxies — and shows what shifted in the past week.

---

## The Proxy Map

We're using ETFs and index futures as stand-ins for macro factors:

| Ticker | What It Proxies |
|--------|----------------|
| SPY | US equities — S&P 500 |
| IWM | Risk appetite — Russell 2000 small caps |
| QQQ | Growth / tech — Nasdaq 100 |
| TLT | Long-duration rates — 20Y+ Treasuries |
| IEF | 10-year note — 7–10Y Treasuries |
| GLD | Gold / real assets / fear hedge |
| DXY | US dollar strength (DX-Y.NYB) |

None of these are the factor itself — SPY isn't the economy, TLT isn't the
10-year yield. But they're liquid, daily-frequency instruments that move with
the factor we care about, and they're free to pull via Yahoo Finance.

---

## The Tool

```cmd
python tools/correlation_matrix.py
```

```text
Fetching prices: SPY, IWM, QQQ, TLT, IEF, GLD, DX-Y.NYB
  Date range: [ACTUAL_START_DATE] to [ACTUAL_END_DATE]

  OK  SPY           [N] trading days
  OK  IWM           [N] trading days
  OK  QQQ           [N] trading days
  OK  TLT           [N] trading days
  OK  IEF           [N] trading days
  OK  GLD           [N] trading days
  OK  DX-Y.NYB      [N] trading days

Top 5 movers (prior → current):
[PASTE ACTUAL TOP-MOVERS OUTPUT HERE]

Chart saved -> .tmp/correlation_matrix_[DATE].png
```

The script fetches 400 calendar days of daily closes, computes log returns,
then slices two 63-trading-day windows: one ending today and one ending five
trading days ago. It computes a Pearson correlation matrix for each window,
subtracts them to get the delta, and renders all three as a single figure.

The window, offset, and ticker list are all runtime arguments — this script
will be the basis for all correlation analysis going forward.

---

## The Current Snapshot

![Correlation Matrix — [CURRENT_DATE_WINDOW] vs [PRIOR_DATE_WINDOW]](CHART_IMAGE)

**Reading the chart:** Panel 1 is the current 63-day correlation structure.
Panel 2 is the same window shifted back one week. Panel 3 is the difference —
green means the pair became more correlated this week, red means they diverged.

**What the current matrix shows:**

[Write 3–4 sentences describing the dominant clusters visible in Panel 1.
Example structure: "Equities are tightly clustered — SPY, IWM, and QQQ are
all correlated above X.XX with each other. TLT and IEF move nearly in lockstep
at X.XX, as expected for instruments on the same curve. Gold's relationship
with equities sits at X.XX — [interpret: slight positive means risk-on, near
zero means it's acting as an independent factor, negative means it's pricing
fear]."]

**What changed this week (Panel 3):**

[Write 2–3 sentences on the delta. Focus on the top 2 movers from the
terminal output. Example: "The biggest shift was [PAIR_1]: correlation moved
from [PRIOR] to [CURRENT], a delta of [DELTA]. This means [interpret].
[PAIR_2] also moved noticeably: [PRIOR] → [CURRENT] ([DELTA])."]

---

## Bottom Line

[Write 2–3 sentences synthesizing the current regime. Answer: what is the
market's correlation structure telling us right now? Is this a risk-on
environment where everything moves together? A fragmented market where
traditional safe havens are diverging? A transition? Use the actual matrix
values to be specific, not generic.]

---

<a href="https://www.buymeacoffee.com/DeltanTheta" target="_blank">
<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
     alt="Buy Me A Coffee"
     style="height: 60px !important; width: 217px !important;" />
</a>
```

> **Image embedding note:** The chart image line `![...](CHART_IMAGE)` needs
> to be replaced with an embedded base64 data URI before posting. Use the same
> approach as other posts — `substack_post.py` handles this conversion automatically
> when it encounters a `.png` path in the markdown.
>
> Replace `CHART_IMAGE` with the relative path to the PNG:
> `.tmp/correlation_matrix_<DATE>.png`

- [ ] **Step 3: Commit**

```bash
cd e:/DnT && git add drafts/post_12_correlation_map.md
git commit -m "feat: add post #12 draft — correlation map"
```

---

## Self-Review Checklist

- [x] **Spec coverage:**
  - `tools/correlation_matrix.py` with all specified args → Tasks 1–4
  - 3-panel heatmap (current / prior / delta) → Task 3
  - `--labels` override → Task 4 (main)
  - `workflows/correlation_matrix.md` → Task 6
  - `drafts/post_12_correlation_map.md` → Task 7
  - Post includes CLI + terminal output → Task 7 template
  - Post includes BMC footer → Task 7 template
  - IEF as 10Y proxy, DX-Y.NYB as DXY → DEFAULT_TICKERS in Task 1

- [x] **No placeholders in code:** All function signatures, logic, and CLI args are fully specified.

- [x] **Type consistency:**
  - `fetch_closes` returns `pd.DataFrame` (wide: date × ticker)
  - `compute_log_returns` takes and returns `pd.DataFrame`
  - `correlation_window` takes `pd.DataFrame`, returns `pd.DataFrame`
  - `plot_three_panel` takes three `pd.DataFrame` + `dict[str, str]` + three `str` — consistent across Tasks 3 and 4
  - `print_top_movers` takes two `pd.DataFrame` — consistent across Tasks 2 and 4
