# Post 20: Reading Rotation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `tools/flow_trend.py` and write `drafts/post_20_reading_rotation.md`.

**Architecture:** `flow_trend.py` reads the latest `.tmp/capital_flows_*.csv` produced by `capital_flows.py`, slices to the last N trading days, and renders a 3-panel stacked matplotlib figure (Cyclicals / Defensives / Macro Proxies), each panel showing 30-day CMF over time as colored lines. No network calls — pure CSV-to-chart pipeline. The post draft runs both tools and embeds their actual output.

**Tech Stack:** Python 3.11+, pandas, matplotlib, argparse, pathlib, glob. No yfinance, no requests, no new dependencies.

## Global Constraints

- Do not modify `tools/capital_flows.py` or `tools/sector_money_flow.py`
- No new API keys or network calls — reads existing `.tmp/capital_flows_*.csv` only
- Matplotlib backend must be set to `"Agg"` (non-interactive) before importing pyplot
- CLI commands in the post must have no inline `#` comments — user runs cmd.exe where `#` is not a comment delimiter
- Chart embedded in draft as `.tmp/` relative path in markdown image syntax
- No paywall in post 20
- Post byline: `*Written by Claude with oversight.*`
- Navigation footer: `← Post 19: The Flow Lens | Post 21: Divergence Signals →`
- BMC button at end: `[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)`
- Tests live in `tests/test_flow_trend.py`; follow the pattern in `tests/test_capital_flows.py`

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `tools/flow_trend.py` | Create | 3-panel CMF trend chart tool |
| `tests/test_flow_trend.py` | Create | Unit + integration tests |
| `drafts/post_20_reading_rotation.md` | Create | Post draft with embedded CLI output and chart |

---

## Task 1: flow_trend.py — data loading functions + tests

**Files:**
- Create: `tools/flow_trend.py`
- Create: `tests/test_flow_trend.py`

**Interfaces:**
- Produces: `find_latest_csv(tmp_dir: str) -> str`, `load_csv(path: str) -> pd.DataFrame`, `slice_lookback(df: pd.DataFrame, n: int) -> pd.DataFrame`

---

- [ ] **Step 1: Write the failing tests**

Create `tests/test_flow_trend.py`:

```python
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def make_mock_csv(tmp_path, filename: str, n: int = 60) -> Path:
    """Write a minimal capital_flows CSV to tmp_path and return its path."""
    ALL_TICKERS = [
        "XLE", "XLI", "XLB", "XLY", "XLK",
        "XLP", "XLU", "XLV", "XLRE", "XLC",
        "XLF", "TLT", "GLD",
    ]
    dates = pd.date_range("2025-01-01", periods=n, freq="B")
    data = {}
    for t in ALL_TICKERS:
        for w in [5, 15, 30]:
            data[f"{t}_cmf{w}"] = np.random.randn(n) * 0.1
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date"
    csv_path = tmp_path / filename
    df.to_csv(csv_path)
    return csv_path


# ── find_latest_csv ───────────────────────────────────────────────────────────

def test_find_latest_csv_returns_most_recent(tmp_path):
    from tools.flow_trend import find_latest_csv
    make_mock_csv(tmp_path, "capital_flows_20250101.csv")
    make_mock_csv(tmp_path, "capital_flows_20250110.csv")
    result = find_latest_csv(str(tmp_path))
    assert result.endswith("capital_flows_20250110.csv")


def test_find_latest_csv_exits_when_none(tmp_path):
    from tools.flow_trend import find_latest_csv
    with pytest.raises(SystemExit):
        find_latest_csv(str(tmp_path))


# ── load_csv ──────────────────────────────────────────────────────────────────

def test_load_csv_returns_datetime_index(tmp_path):
    from tools.flow_trend import load_csv
    csv_path = make_mock_csv(tmp_path, "capital_flows_20250110.csv")
    df = load_csv(str(csv_path))
    assert isinstance(df.index, pd.DatetimeIndex)


def test_load_csv_has_expected_columns(tmp_path):
    from tools.flow_trend import load_csv
    csv_path = make_mock_csv(tmp_path, "capital_flows_20250110.csv")
    df = load_csv(str(csv_path))
    assert "XLK_cmf30" in df.columns
    assert "GLD_cmf30" in df.columns


# ── slice_lookback ────────────────────────────────────────────────────────────

def test_slice_lookback_returns_last_n_rows():
    from tools.flow_trend import slice_lookback
    dates = pd.date_range("2025-01-01", periods=100, freq="B")
    df = pd.DataFrame({"XLK_cmf30": np.random.randn(100)}, index=dates)
    result = slice_lookback(df, 30)
    assert len(result) == 30
    assert result.index[-1] == df.index[-1]


def test_slice_lookback_clips_to_available_rows():
    from tools.flow_trend import slice_lookback
    dates = pd.date_range("2025-01-01", periods=10, freq="B")
    df = pd.DataFrame({"XLK_cmf30": np.random.randn(10)}, index=dates)
    result = slice_lookback(df, 60)
    assert len(result) == 10
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_flow_trend.py -v
```

Expected: `ModuleNotFoundError` or `ImportError` — `tools.flow_trend` does not exist yet.

- [ ] **Step 3: Implement the data loading functions**

Create `tools/flow_trend.py` with all imports included upfront (matplotlib is imported here so tests don't fail when Task 2 appends render_trend_chart):

```python
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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_flow_trend.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```
git add tools/flow_trend.py tests/test_flow_trend.py
git commit -m "feat: add flow_trend.py data loading functions + tests"
```

---

## Task 2: flow_trend.py — chart rendering + CLI + integration test

**Files:**
- Modify: `tools/flow_trend.py` (add `render_trend_chart`, `main`)
- Modify: `tests/test_flow_trend.py` (add chart + CLI tests)

**Interfaces:**
- Consumes: `load_csv`, `slice_lookback`, `find_latest_csv` from Task 1
- Produces: `render_trend_chart(df: pd.DataFrame, as_of: str, out_path: str) -> None`, `main() -> None`

---

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_flow_trend.py`:

```python
# ── render_trend_chart ────────────────────────────────────────────────────────

def test_render_trend_chart_creates_file(tmp_path):
    from tools.flow_trend import render_trend_chart
    csv_path = make_mock_csv(tmp_path, "capital_flows_20250110.csv", n=60)
    df = pd.read_csv(str(csv_path), index_col=0, parse_dates=True)
    out_path = str(tmp_path / "test_chart.png")
    render_trend_chart(df, as_of="2025-03-31", out_path=out_path)
    assert Path(out_path).exists()
    assert Path(out_path).stat().st_size > 10_000  # non-trivial PNG


def test_render_trend_chart_handles_missing_column(tmp_path):
    """Chart should not crash if a ticker column is absent from the CSV."""
    from tools.flow_trend import render_trend_chart
    dates = pd.date_range("2025-01-01", periods=60, freq="B")
    df = pd.DataFrame({"XLK_cmf30": [0.1] * 60}, index=dates)
    out_path = str(tmp_path / "partial_chart.png")
    render_trend_chart(df, as_of="2025-03-31", out_path=out_path)
    assert Path(out_path).exists()


# ── CLI integration ───────────────────────────────────────────────────────────

def test_cli_runs_end_to_end(tmp_path):
    import subprocess
    csv_path = make_mock_csv(tmp_path, "capital_flows_20250110.csv", n=60)
    out_path = str(tmp_path / "out.png")
    result = subprocess.run(
        [sys.executable, "tools/flow_trend.py",
         "--csv", str(csv_path),
         "--out", out_path,
         "--lookback", "30"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "Chart saved" in result.stdout
    assert Path(out_path).exists()
```

- [ ] **Step 2: Run new tests to verify they fail**

```
pytest tests/test_flow_trend.py::test_render_trend_chart_creates_file tests/test_flow_trend.py::test_cli_runs_end_to_end -v
```

Expected: `AttributeError` — `render_trend_chart` not defined yet.

- [ ] **Step 3: Implement render_trend_chart and main**

Append to `tools/flow_trend.py` (after `slice_lookback`):

```python
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
    print(f"Chart saved → {out_path}")


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
```

- [ ] **Step 4: Run all tests**

```
pytest tests/test_flow_trend.py -v
```

Expected: all 10 tests pass.

- [ ] **Step 5: Run the tool against real data to verify the chart**

```
python tools/flow_trend.py
```

Expected output (exact date will differ):
```
Flow Trend Chart  —  2026-06-22  (60-day lookback)
Chart saved → e:\DnT\.tmp\flow_trend_20260622.png
```

Open `.tmp/flow_trend_<date>.png` and verify: 3 stacked panels, labeled lines, zero line visible, x-axis shows month labels, y-axis clipped to ±0.5.

- [ ] **Step 6: Commit**

```
git add tools/flow_trend.py tests/test_flow_trend.py
git commit -m "feat: add flow_trend.py chart rendering and CLI"
```

---

## Task 3: Post 20 draft

**Files:**
- Create: `drafts/post_20_reading_rotation.md`

**Interfaces:**
- Consumes: `tools/capital_flows.py --report` (watchlist output), `tools/flow_trend.py` (chart)

---

- [ ] **Step 1: Run both tools and capture output**

Run the watchlist to refresh context (copy the terminal output — it goes in the post):
```
python tools/capital_flows.py
```

Run the trend tool (copy the one-line output — it confirms the chart path):
```
python tools/flow_trend.py
```

Note the chart path (e.g. `.tmp/flow_trend_20260622.png`).

- [ ] **Step 2: Write the post draft**

Create `drafts/post_20_reading_rotation.md` with this structure. Fill in the `[PASTE ...]` sections with actual terminal output from Step 1.

```markdown
# Reading Rotation: How 60 Days of Flow Got Us Here

*DeltaTheta | Post 20 of the Build Series*

*Written by Claude with oversight.*

Post 19 introduced the flow lens: a snapshot of where capital is sitting right
now, ranked by conviction across three timeframes. That snapshot told you what
to overweight and underweight today. It didn't tell you how we got here.

This post zooms out. The same data that produces the ranked watchlist also
contains 869 trading days of CMF history. Running it as a time series shows you
which sectors have been building flow for weeks, which just reversed, and which
have been consistently leaking capital for a quarter. That context is what turns
a positioning call into a rotation read.

---

## The Rotation Cycle

Sector rotation describes the tendency for capital to move through sectors in a
predictable sequence tied to the economic cycle. The pattern — attributed to
the Merrill Lynch Investment Clock and popularized by strategists like Sam Stovall
— runs roughly as follows:

**Early recovery:** Consumer Discretionary and Technology lead. Risk appetite
returns, earnings expectations rise, cyclicals attract capital first.

**Mid-cycle expansion:** Industrials, Materials, and Energy outperform as the
physical economy catches up to financial conditions. Flow shifts from growth
into volume-driven sectors.

**Late cycle:** Energy and Materials continue, but Defensives — Consumer Staples,
Health Care, Utilities — begin to attract capital as the expansion matures and
investors hedge against a turn. Financial conditions tighten.

**Contraction:** Defensives hold while cyclicals and rate-sensitive sectors
(Real Estate, Discretionary) sell off. Fixed Income attracts inflows as yields
fall. Gold may rise depending on whether the contraction is inflationary or
deflationary.

The rotation doesn't always follow this sequence cleanly or on the same schedule.
But when you plot 30-day CMF over time across the three groups — cyclicals,
defensives, macro proxies — the relative flow direction tells you where capital
thinks we are in that sequence, without requiring anyone to call the cycle.

---

## The Tool

`flow_trend.py` reads the CSV produced by `capital_flows.py` and plots 30-day CMF
over the past 60 trading days for all 13 proxies, organized into three panels.

```
python tools/capital_flows.py
python tools/flow_trend.py
```

```
[PASTE actual terminal output from both commands here]
```

---

## Reading the Three Panels

![Capital Flow Trends — 30-Day CMF, 60-Day Lookback](.tmp/flow_trend_YYYYMMDD.png)

### Cyclicals Panel

[Write 2–3 paragraphs interpreting the Cyclicals panel (XLE, XLI, XLB, XLY, XLK).
Key questions: Which lines are trending up vs down over the 60-day window?
Which crossed zero recently (a flip from outflow to inflow or vice versa)?
Which have been consistently negative or positive throughout? What does the
spread between the highest and lowest cyclical tell you about rotation within
the group?]

### Defensives Panel

[Write 2–3 paragraphs interpreting the Defensives panel (XLP, XLU, XLV, XLRE, XLC).
Key questions: Are defensives gaining relative to cyclicals (late-cycle signal)?
Are they uniformly negative (risk-on environment) or mixed? Is Real Estate
tracking interest rate expectations? Is Consumer Staples diverging from
Utilities?]

### Macro Proxies Panel

[Write 2–3 paragraphs interpreting the Macro Proxies panel (XLF, TLT, GLD).
Key questions: Is Financials (XLF) trend positive (credit expansion) or
negative (tightening conditions)? Is TLT trending up (bond demand rising,
rate expectations falling) or down? Is Gold rising with risk-off or selling
off despite equity weakness? What does the relationship between XLF and TLT
say about where we are in the rate cycle?]

---

## Where We Are

[Write one summary paragraph placing the current rotation picture on the cycle
map. Which phase does the combined signal from all three panels suggest?
What's the most important thing to watch for in the next 30–60 days that
would confirm or invalidate the current read?]

---

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

*← [Post 19: The Flow Lens](#) | [Post 21: Divergence Signals →](#)*

— *DeltaTheta*
```

**Important:** Replace `.tmp/flow_trend_YYYYMMDD.png` with the actual filename from Step 1. Replace all `[PASTE ...]` and `[Write ...]` blocks with real content based on the actual chart. Do not leave any brackets in the final draft.

- [ ] **Step 3: Verify the draft reads correctly**

Open `drafts/post_20_reading_rotation.md` and confirm:
- No `[PASTE ...]` or `[Write ...]` placeholders remain
- CLI block contains real terminal output
- Image path points to an existing `.tmp/flow_trend_*.png` file
- Navigation links are present
- BMC footer is present
- No inline `#` comments in code blocks

- [ ] **Step 4: Commit**

```
git add drafts/post_20_reading_rotation.md
git commit -m "feat: add post 20 draft — reading rotation, 60-day CMF trend chart"
```
