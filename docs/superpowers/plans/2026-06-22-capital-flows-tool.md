# Capital Flows Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tools/capital_flows.py` — a multi-timeframe CMF signal tool that outputs a ranked investment positioning watchlist, positioning table, and heatmap chart for 13 domestic US sector/asset-class ETF proxies.

**Architecture:** Single tool file that fetches OHLCV via yfinance, computes 5/15/30-day Chaikin Money Flow for each ticker, derives alignment scores and divergence flags, then renders three output formats. Pure logic functions are separated so they can be unit-tested with synthetic data without network access.

**Tech Stack:** Python 3.11+, yfinance, pandas, numpy, matplotlib, curl_cffi (SSL bypass), pytest

## Global Constraints

- Do NOT modify `tools/sector_money_flow.py` — new tool only
- All market data via yfinance only (no new API keys)
- Same SSL bypass pattern as sector_money_flow.py: `os.environ["CURL_CA_BUNDLE"] = ""`, `ssl._create_default_https_context = ssl._create_unverified_context`, `curl_requests.Session(impersonate="chrome", verify=False)`
- Output files always go to `.tmp/` (create if missing)
- Test file: `tests/test_capital_flows.py`, following the pattern in `tests/test_credit_spreads.py`
- CMF positioning thresholds: OVER = CMF > 0.05, UNDER = CMF < −0.05, NEUT = between
- Divergence thresholds: CMF magnitude > 0.05, price return magnitude > 1% (0.01)
- matplotlib backend must be set to "Agg" before any other matplotlib import

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `tools/capital_flows.py` | Create | Main tool — fetch, compute, derive, output |
| `tests/test_capital_flows.py` | Create | Unit tests for all pure logic functions |

---

### Task 1: Scaffold, data fetch, and CMF computation

**Files:**
- Create: `tools/capital_flows.py`
- Create: `tests/test_capital_flows.py`

**Interfaces:**
- Produces: `fetch(tickers, start, end) -> dict[str, pd.DataFrame]`
- Produces: `compute_cmf(df, window) -> pd.Series` — values in `[-1, +1]`
- Produces: `build_signal_stack(raw, windows=(5,15,30)) -> pd.DataFrame` — MultiIndex columns `(ticker, window)`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_capital_flows.py`:

```python
import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


def make_mock_ohlcv(n: int = 60, close_position: float = 0.8) -> pd.DataFrame:
    """
    close_position: 0.0 = close at low (MFM = -1), 1.0 = close at high (MFM = +1)
    """
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    highs = np.ones(n) * 101.0
    lows = np.ones(n) * 99.0
    closes = lows + (highs - lows) * close_position
    return pd.DataFrame(
        {"High": highs, "Low": lows, "Close": closes, "Volume": np.ones(n) * 1_000_000},
        index=dates,
    )


def test_compute_cmf_positive_when_close_near_high():
    from tools.capital_flows import compute_cmf
    df = make_mock_ohlcv(close_position=0.9)
    cmf = compute_cmf(df, window=5)
    assert cmf.dropna().iloc[-1] > 0


def test_compute_cmf_negative_when_close_near_low():
    from tools.capital_flows import compute_cmf
    df = make_mock_ohlcv(close_position=0.1)
    cmf = compute_cmf(df, window=5)
    assert cmf.dropna().iloc[-1] < 0


def test_compute_cmf_range():
    from tools.capital_flows import compute_cmf
    df = make_mock_ohlcv(close_position=0.5)
    cmf = compute_cmf(df, window=5)
    valid = cmf.dropna()
    assert (valid >= -1.0).all() and (valid <= 1.0).all()


def test_build_signal_stack_shape():
    from tools.capital_flows import compute_cmf, build_signal_stack
    raw = {"XLF": make_mock_ohlcv(60), "XLK": make_mock_ohlcv(60)}
    wide = build_signal_stack(raw, windows=(5, 15, 30))
    assert ("XLF", 5) in wide.columns
    assert ("XLK", 30) in wide.columns
    assert wide.shape[1] == 6  # 2 tickers × 3 windows
```

- [ ] **Step 2: Run tests — verify they fail**

```
pytest tests/test_capital_flows.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` (module doesn't exist yet)

- [ ] **Step 3: Create `tools/capital_flows.py` with fetch, CMF, and signal stack**

```python
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
```

- [ ] **Step 4: Run tests — verify they pass**

```
pytest tests/test_capital_flows.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```
git add tools/capital_flows.py tests/test_capital_flows.py
git commit -m "feat: add capital_flows scaffold with fetch and CMF computation"
```

---

### Task 2: Signal derivation — positioning, alignment, divergence, position call

**Files:**
- Modify: `tools/capital_flows.py` — add four pure functions
- Modify: `tests/test_capital_flows.py` — add tests for each

**Interfaces:**
- Consumes: `compute_cmf()` outputs (float CMF values and pd.Series)
- Produces: `derive_positioning(cmf) -> str` — "OVER" | "NEUT" | "UNDER"
- Produces: `derive_alignment(pos5, pos15, pos30) -> tuple[int, str]` — (count, arrows)
- Produces: `compute_price_return(ohlcv, n_days) -> float`
- Produces: `derive_divergence(cmf15, price_return) -> str` — "[DIV↓]" | "[DIV↑]" | ""
- Produces: `make_position_call(pos5, pos15, pos30) -> str`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_capital_flows.py`:

```python
# ── positioning ──────────────────────────────────────────────────────────────

def test_derive_positioning_over():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(0.10) == "OVER"

def test_derive_positioning_under():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(-0.10) == "UNDER"

def test_derive_positioning_neut_positive_edge():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(0.03) == "NEUT"

def test_derive_positioning_neut_negative_edge():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(-0.03) == "NEUT"

def test_derive_positioning_nan():
    from tools.capital_flows import derive_positioning
    assert derive_positioning(float("nan")) == "NEUT"

# ── alignment ─────────────────────────────────────────────────────────────────

def test_derive_alignment_all_over():
    from tools.capital_flows import derive_alignment
    count, arrows = derive_alignment("OVER", "OVER", "OVER")
    assert count == 3
    assert arrows == "▲▲▲"

def test_derive_alignment_all_under():
    from tools.capital_flows import derive_alignment
    count, arrows = derive_alignment("UNDER", "UNDER", "UNDER")
    assert count == 3
    assert arrows == "▼▼▼"

def test_derive_alignment_mixed():
    from tools.capital_flows import derive_alignment
    count, arrows = derive_alignment("OVER", "NEUT", "UNDER")
    assert count == 1
    assert arrows == "▲→▼"

def test_derive_alignment_two_over():
    from tools.capital_flows import derive_alignment
    count, arrows = derive_alignment("OVER", "OVER", "NEUT")
    assert count == 2
    assert arrows == "▲▲→"

# ── price return ──────────────────────────────────────────────────────────────

def test_compute_price_return_positive():
    from tools.capital_flows import compute_price_return
    df = make_mock_ohlcv(60, close_position=0.5)
    # All closes are equal (flat synthetic data) so return ≈ 0
    ret = compute_price_return(df, 15)
    assert isinstance(ret, float)

def test_compute_price_return_insufficient_data():
    from tools.capital_flows import compute_price_return
    df = make_mock_ohlcv(10, close_position=0.5)
    ret = compute_price_return(df, 15)
    assert np.isnan(ret)

# ── divergence ────────────────────────────────────────────────────────────────

def test_derive_divergence_distribution():
    from tools.capital_flows import derive_divergence
    # CMF negative, price up = distribution
    assert derive_divergence(-0.15, 0.03) == "[DIV↓]"

def test_derive_divergence_accumulation():
    from tools.capital_flows import derive_divergence
    # CMF positive, price down = accumulation
    assert derive_divergence(0.15, -0.03) == "[DIV↑]"

def test_derive_divergence_none_when_aligned():
    from tools.capital_flows import derive_divergence
    assert derive_divergence(0.15, 0.03) == ""
    assert derive_divergence(-0.15, -0.03) == ""

def test_derive_divergence_none_below_threshold():
    from tools.capital_flows import derive_divergence
    # CMF too small to trigger
    assert derive_divergence(-0.02, 0.03) == ""

# ── position call ─────────────────────────────────────────────────────────────

def test_position_call_all_over():
    from tools.capital_flows import make_position_call
    assert make_position_call("OVER", "OVER", "OVER") == "OVERWEIGHT  2W–90D"

def test_position_call_all_under():
    from tools.capital_flows import make_position_call
    assert make_position_call("UNDER", "UNDER", "UNDER") == "UNDERWEIGHT  2W–90D"

def test_position_call_medium_long_over():
    from tools.capital_flows import make_position_call
    assert make_position_call("NEUT", "OVER", "OVER") == "OVERWEIGHT  30D–90D"

def test_position_call_short_medium_over():
    from tools.capital_flows import make_position_call
    assert make_position_call("OVER", "OVER", "NEUT") == "OVERWEIGHT  2W–30D"

def test_position_call_split_over():
    from tools.capital_flows import make_position_call
    # 5D=OVER, 15D=NEUT, 30D=OVER — non-consecutive, ambiguous
    assert make_position_call("OVER", "NEUT", "OVER") == "HOLD / WATCH"

def test_position_call_mixed():
    from tools.capital_flows import make_position_call
    assert make_position_call("OVER", "NEUT", "UNDER") == "HOLD / WATCH"
```

- [ ] **Step 2: Run tests — verify they fail**

```
pytest tests/test_capital_flows.py -v -k "positioning or alignment or price_return or divergence or position_call"
```

Expected: all FAIL with ImportError or AttributeError

- [ ] **Step 3: Add the four functions to `tools/capital_flows.py`**

Add after `build_signal_stack()`:

```python
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
```

- [ ] **Step 4: Run tests — verify they pass**

```
pytest tests/test_capital_flows.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```
git add tools/capital_flows.py tests/test_capital_flows.py
git commit -m "feat: add signal derivation — positioning, alignment, divergence, position call"
```

---

### Task 3: Snapshot assembly

**Files:**
- Modify: `tools/capital_flows.py` — add `derive_snapshot()`
- Modify: `tests/test_capital_flows.py` — add snapshot test

**Interfaces:**
- Consumes: `build_signal_stack()`, `compute_price_return()`, `derive_positioning()`, `derive_alignment()`, `derive_divergence()`, `make_position_call()`
- Produces: `derive_snapshot(wide, raw, tickers) -> pd.DataFrame` — one row per ticker, sorted by cmf15 descending

Snapshot DataFrame columns: `ticker`, `label`, `cmf5`, `cmf15`, `cmf30`, `pos5`, `pos15`, `pos30`, `align_count`, `align_arrows`, `price_return_15d`, `div_flag`, `position_call`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_capital_flows.py`:

```python
def test_derive_snapshot_columns_and_sort():
    from tools.capital_flows import build_signal_stack, derive_snapshot
    raw = {
        "XLF": make_mock_ohlcv(60, close_position=0.9),  # strong positive CMF
        "XLE": make_mock_ohlcv(60, close_position=0.1),  # strong negative CMF
    }
    tickers = {"XLF": "Financials", "XLE": "Energy"}
    wide = build_signal_stack(raw, windows=(5, 15, 30))
    snap = derive_snapshot(wide, raw, tickers)

    expected_cols = {
        "ticker", "label", "cmf5", "cmf15", "cmf30",
        "pos5", "pos15", "pos30", "align_count", "align_arrows",
        "price_return_15d", "div_flag", "position_call",
    }
    assert expected_cols.issubset(set(snap.columns))
    # XLF (positive flow) should rank above XLE (negative flow)
    assert snap.iloc[0]["ticker"] == "XLF"
    assert snap.iloc[1]["ticker"] == "XLE"
```

- [ ] **Step 2: Run test — verify it fails**

```
pytest tests/test_capital_flows.py::test_derive_snapshot_columns_and_sort -v
```

Expected: FAIL with AttributeError

- [ ] **Step 3: Add `derive_snapshot()` to `tools/capital_flows.py`**

Add after `make_position_call()`:

```python
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
    last = wide.dropna(how="all").iloc[-1]
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
```

- [ ] **Step 4: Run tests — verify all pass**

```
pytest tests/test_capital_flows.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```
git add tools/capital_flows.py tests/test_capital_flows.py
git commit -m "feat: add derive_snapshot — assembles per-ticker signal rows sorted by 15D CMF"
```

---

### Task 4: Ranked watchlist output (`--report`)

**Files:**
- Modify: `tools/capital_flows.py` — add `print_watchlist()`
- Modify: `tests/test_capital_flows.py` — add watchlist output test

**Interfaces:**
- Consumes: `derive_snapshot()` output
- Produces: `print_watchlist(snap, as_of) -> None` — prints ranked watchlist to stdout

- [ ] **Step 1: Write the failing test**

Add to `tests/test_capital_flows.py`:

```python
def test_print_watchlist_contains_key_fields(capsys):
    from tools.capital_flows import build_signal_stack, derive_snapshot, print_watchlist
    raw = {
        "XLF": make_mock_ohlcv(60, close_position=0.9),
        "XLE": make_mock_ohlcv(60, close_position=0.1),
    }
    tickers = {"XLF": "Financials", "XLE": "Energy"}
    wide = build_signal_stack(raw, windows=(5, 15, 30))
    snap = derive_snapshot(wide, raw, tickers)
    print_watchlist(snap, as_of="2026-06-22")
    captured = capsys.readouterr().out
    assert "Capital Flow Watchlist" in captured
    assert "Financials" in captured
    assert "Energy" in captured
    assert "OVERWEIGHT" in captured or "UNDERWEIGHT" in captured or "HOLD" in captured
    assert "▲" in captured or "▼" in captured or "→" in captured
```

- [ ] **Step 2: Run test — verify it fails**

```
pytest tests/test_capital_flows.py::test_print_watchlist_contains_key_fields -v
```

Expected: FAIL with AttributeError

- [ ] **Step 3: Add `print_watchlist()` to `tools/capital_flows.py`**

Add after `derive_snapshot()`:

```python
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
            f"  {row['cmf5']:>+7.4f}"
            f"  {row['cmf15']:>+7.4f}"
            f"  {row['cmf30']:>+7.4f}"
            f"  {row['align_arrows']:>5}"
            f"  {row['position_call']}{div}"
        )
        print(line)
    print()
```

- [ ] **Step 4: Run tests — verify all pass**

```
pytest tests/test_capital_flows.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```
git add tools/capital_flows.py tests/test_capital_flows.py
git commit -m "feat: add print_watchlist — ranked CMF watchlist with positioning calls"
```

---

### Task 5: Positioning table (`--table`) and heatmap chart (`--chart`)

**Files:**
- Modify: `tools/capital_flows.py` — add `print_table()` and `render_heatmap()`
- Modify: `tests/test_capital_flows.py` — add table and chart tests

**Interfaces:**
- Consumes: `derive_snapshot()` output
- Produces: `print_table(snap, as_of) -> None`
- Produces: `render_heatmap(snap, as_of, out_path) -> None` — saves PNG to `out_path`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_capital_flows.py`:

```python
def test_print_table_contains_over_under_neut(capsys):
    from tools.capital_flows import build_signal_stack, derive_snapshot, print_table
    raw = {
        "XLF": make_mock_ohlcv(60, close_position=0.9),
        "XLE": make_mock_ohlcv(60, close_position=0.1),
    }
    tickers = {"XLF": "Financials", "XLE": "Energy"}
    wide = build_signal_stack(raw, windows=(5, 15, 30))
    snap = derive_snapshot(wide, raw, tickers)
    print_table(snap, as_of="2026-06-22")
    captured = capsys.readouterr().out
    assert "2W" in captured
    assert "30D" in captured
    assert "90D" in captured
    assert any(label in captured for label in ("OVER", "NEUT", "UNDER"))


def test_render_heatmap_creates_file():
    import tempfile
    import matplotlib
    matplotlib.use("Agg")
    from tools.capital_flows import build_signal_stack, derive_snapshot, render_heatmap
    raw = {
        "XLF": make_mock_ohlcv(60, close_position=0.9),
        "XLE": make_mock_ohlcv(60, close_position=0.1),
    }
    tickers = {"XLF": "Financials", "XLE": "Energy"}
    wide = build_signal_stack(raw, windows=(5, 15, 30))
    snap = derive_snapshot(wide, raw, tickers)
    with tempfile.TemporaryDirectory() as d:
        from pathlib import Path
        out = Path(d) / "heatmap.png"
        render_heatmap(snap, as_of="2026-06-22", out_path=str(out))
        assert out.exists() and out.stat().st_size > 0
```

- [ ] **Step 2: Run tests — verify they fail**

```
pytest tests/test_capital_flows.py::test_print_table_contains_over_under_neut tests/test_capital_flows.py::test_render_heatmap_creates_file -v
```

Expected: FAIL with AttributeError

- [ ] **Step 3: Add `print_table()` and `render_heatmap()` to `tools/capital_flows.py`**

Add after `print_watchlist()`:

```python
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


COLOR_POS  = "#2563EB"   # blue  — inflow
COLOR_NEG  = "#DC2626"   # red   — outflow
COLOR_ZERO = "#6B7280"   # gray  — near zero


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

    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved → {out_path}")
```

- [ ] **Step 4: Run tests — verify all pass**

```
pytest tests/test_capital_flows.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```
git add tools/capital_flows.py tests/test_capital_flows.py
git commit -m "feat: add print_table and render_heatmap output formats"
```

---

### Task 6: CSV save and CLI wiring — end-to-end

**Files:**
- Modify: `tools/capital_flows.py` — add `save()` and `main()`

**Interfaces:**
- Consumes: all previously defined functions
- Produces: `save(wide, path) -> None` — writes flattened CSV to `.tmp/`
- Produces: `main() -> None` — argparse CLI, ties everything together

- [ ] **Step 1: Add `save()` and `main()` to `tools/capital_flows.py`**

Add at the end of the file:

```python
def save(wide: pd.DataFrame, path: str) -> None:
    """Saves flattened wide CMF time series to CSV. Columns: XLF_cmf5, XLF_cmf15, ..."""
    flat = wide.copy()
    flat.columns = [f"{ticker}_cmf{window}" for ticker, window in flat.columns]
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

    as_of = str(wide.dropna(how="all").index[-1].date())
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
```

- [ ] **Step 2: Run the full test suite**

```
pytest tests/test_capital_flows.py -v
```

Expected: all PASS

- [ ] **Step 3: Smoke test — run the tool end-to-end**

```
python tools/capital_flows.py --all
```

Expected output (approximate):
```
Fetching OHLCV for 13 tickers...
  OK  XLB    ...
  ...
  OK  GLD    ...

Computing (5, 15, 30)-day CMF...

Saved N rows × 39 cols → .tmp/capital_flows_<date>.csv

Capital Flow Watchlist  —  <date>
Horizon: 2W / 30D / 90D

  Sector                    5D       15D      30D   Align  Position
  ──────────────────────────────────────────────────────────────────────────────
  <sectors ranked by 15D CMF, with arrows and calls>
  ...

Positioning Table  —  <date>

  Sector                      2W     30D     90D
  ────────────────────────────────────────────────
  ...

Chart saved → .tmp/capital_flows_chart_<date>.png
```

If any ticker fails to fetch, it is skipped with a WARN to stderr — this is expected behavior, not a bug.

- [ ] **Step 4: Verify chart and CSV exist**

```
python -c "
from pathlib import Path
from datetime import datetime
d = datetime.today().strftime('%Y%m%d')
csv  = Path(f'.tmp/capital_flows_{d}.csv')
png  = Path(f'.tmp/capital_flows_chart_{d}.png')
print('CSV:', csv.exists(), csv.stat().st_size if csv.exists() else 0, 'bytes')
print('PNG:', png.exists(), png.stat().st_size if png.exists() else 0, 'bytes')
"
```

Expected: both files exist with size > 0

- [ ] **Step 5: Commit**

```
git add tools/capital_flows.py
git commit -m "feat: add save and CLI wiring — capital_flows.py complete"
```

---

## Self-Review Checklist

- **Spec coverage:**
  - ✅ `tools/capital_flows.py` — new tool, does not touch `sector_money_flow.py`
  - ✅ Tickers: all 11 SPDRs + TLT + GLD
  - ✅ Signal stack: 5/15/30-day CMF
  - ✅ Positioning: OVER/NEUT/UNDER with ±0.05 threshold
  - ✅ Alignment score and arrow string
  - ✅ Divergence detection (CMF vs price direction)
  - ✅ Position call with horizon range string
  - ✅ `--report` ranked watchlist (default)
  - ✅ `--table` positioning grid
  - ✅ `--chart` heatmap PNG
  - ✅ `--all` combines all three
  - ✅ CSV always saved to `.tmp/capital_flows_<date>.csv`
  - ✅ `--start`, `--end`, `--out`, `--chart-out` overrides
  - ✅ Same SSL/curl_cffi pattern as existing tools
  - ✅ Tests for all pure logic functions with synthetic data

- **Type consistency:**
  - `derive_snapshot()` uses `WINDOWS` constant for default — matches what `build_signal_stack()` uses
  - `derive_snapshot()` calls `compute_price_return(raw[ticker], w15)` — `w15` is `windows[1]` = 15
  - `render_heatmap()` references `snap["cmf5"]`, `snap["cmf15"]`, `snap["cmf30"]` — all present in `derive_snapshot()` output
  - `print_table()` references `snap["pos5"]`, `snap["pos15"]`, `snap["pos30"]` — all present

- **No placeholders:** All steps contain complete code.
