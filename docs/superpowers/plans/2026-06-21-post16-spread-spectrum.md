# Post 16 — Spread Spectrum Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `tools/credit_spreads.py` with a differential summary row and two new chart outputs (two-panel time-series + tier stack), then write the Post 16 draft using live tool output.

**Architecture:** All tool changes are surgical additions to `credit_spreads.py` — no new files, no new CLI flags. `print_summary()` detects HY+IG presence and appends a differential row automatically. `make_chart()` detects the same and splits into a two-panel figure. `make_stack_chart()` is a new function wired into `main()`. The post draft is a new markdown file under `drafts/`.

**Tech Stack:** Python 3.10+, matplotlib, pandas, numpy, fredapi, pytest

## Global Constraints

- No new CLI flags — differential row and stack chart appear automatically when HY and IG are both fetched
- Dark background `#0a0f1e`, grid `#1e2a3a` — match existing chart style exactly
- Series colors: HY `#f5a623`, IG `#4a9eff`, CCC `#e05c5c` — unchanged from existing
- All chart output to `.tmp/`, filename pattern `credit_spreads_YYYYMMDD.png` / `credit_spreads_stack_YYYYMMDD.png`
- Post tone: same as post 15 — precise, not academic, two reads on interpretation, no position taken
- Post ends with BMC button: `[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)`
- Run the tool fresh (live FRED data) when writing the post draft

---

## File Map

| File | Action | Responsibility |
| ------ | -------- | ------------- |
| `tools/credit_spreads.py` | Modify | Add differential row, two-panel chart, stack chart |
| `tests/test_credit_spreads.py` | Create | Behavioral tests for new logic |
| `tests/conftest.py` | Create | sys.path setup so `tools` is importable |
| `drafts/post_16_spread_spectrum.md` | Create | Full post draft with live data embedded |

---

## Task 1: Test scaffold + differential row in `print_summary()`

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_credit_spreads.py`
- Modify: `tools/credit_spreads.py` — `print_summary()` only

**Interfaces:**
- Produces: `print_summary(df, series_keys)` — unchanged signature, new behavior when `"HY"` and `"IG"` both in `df.columns`

- [ ] **Step 1: Create `tests/conftest.py`**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_credit_spreads.py`:

```python
import io
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def make_mock_df(series=("HY", "IG")):
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    data = {}
    if "HY" in series:
        data["HY"] = np.linspace(3.0, 2.0, 300)
    if "IG" in series:
        data["IG"] = np.linspace(1.5, 0.7, 300)
    if "CCC" in series:
        data["CCC"] = np.linspace(9.0, 7.0, 300)
    return pd.DataFrame(data, index=dates)


def capture_print_summary(df, keys):
    from tools.credit_spreads import print_summary
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        print_summary(df, keys)
    finally:
        sys.stdout = old
    return buf.getvalue()


def test_differential_row_appears_when_hy_and_ig_present():
    df = make_mock_df(("HY", "IG"))
    out = capture_print_summary(df, ["HY", "IG"])
    assert "HY" in out
    assert "Quality Premium" in out


def test_differential_row_absent_when_only_hy():
    df = make_mock_df(("HY",))
    out = capture_print_summary(df, ["HY"])
    assert "Quality Premium" not in out


def test_differential_row_absent_when_only_ig():
    df = make_mock_df(("IG",))
    out = capture_print_summary(df, ["IG"])
    assert "Quality Premium" not in out


def test_differential_value_is_hy_minus_ig():
    df = make_mock_df(("HY", "IG"))
    out = capture_print_summary(df, ["HY", "IG"])
    # Last HY = 2.00, last IG = 0.70, diff = 1.30
    assert "1.30%" in out
```

- [ ] **Step 3: Run tests to confirm they fail**

```
pytest tests/test_credit_spreads.py -v
```

Expected: 4 failures — `Quality Premium` string does not exist yet.

- [ ] **Step 4: Modify `print_summary()` in `tools/credit_spreads.py`**

Find the closing separator lines at the end of `print_summary()`:

```python
    print("=" * 68)
    print("  Source: ICE BofA via FRED  |  OAS = Option-Adjusted Spread over Treasuries\n")
```

Replace with:

```python
    if "HY" in df.columns and "IG" in df.columns:
        hy = df["HY"].dropna()
        ig = df["IG"].dropna()
        common = hy.index.intersection(ig.index)
        diff = hy.loc[common] - ig.loc[common]
        if not diff.empty:
            current_diff = diff.iloc[-1]
            week_ago_diff = diff.iloc[-6] if len(diff) > 6 else diff.iloc[0]
            wow_diff = current_diff - week_ago_diff
            one_year_ago = diff.index[-1] - pd.DateOffset(years=1)
            diff_52w = diff[diff.index >= one_year_ago]
            pctile_diff = percentile_rank(diff, current_diff)
            wow_str = f"{'+' if wow_diff >= 0 else ''}{wow_diff:.2f}"
            print("-" * 68)
            print(
                f"  {'HY–IG Quality Premium':<26} {current_diff:>7.2f}%"
                f" {diff_52w.min():>8.2f}% {diff_52w.max():>8.2f}%"
                f" {pctile_diff:>7.1f}%"
                f" {wow_str:>9}"
            )

    print("=" * 68)
    print("  Source: ICE BofA via FRED  |  OAS = Option-Adjusted Spread over Treasuries\n")
```

- [ ] **Step 5: Run tests — confirm all pass**

```
pytest tests/test_credit_spreads.py -v
```

Expected output:
```
PASSED tests/test_credit_spreads.py::test_differential_row_appears_when_hy_and_ig_present
PASSED tests/test_credit_spreads.py::test_differential_row_absent_when_only_hy
PASSED tests/test_credit_spreads.py::test_differential_row_absent_when_only_ig
PASSED tests/test_credit_spreads.py::test_differential_value_is_hy_minus_ig
```

- [ ] **Step 6: Smoke-test the CLI**

```
python tools/credit_spreads.py --series HY IG
```

Verify the `HY–IG Quality Premium` row appears below the main rows, before the closing `===` line.

- [ ] **Step 7: Commit**

```
git add tests/conftest.py tests/test_credit_spreads.py tools/credit_spreads.py
git commit -m "feat: add HY-IG quality premium row to credit spread snapshot"
```

---

## Task 2: Two-panel `make_chart()` with differential bottom panel

**Files:**
- Modify: `tools/credit_spreads.py` — `make_chart()` only

**Interfaces:**
- Consumes: `make_chart(df, series_keys, recessions, out_path)` — signature unchanged
- Produces: same function, now produces a two-panel figure when HY and IG are both in `df.columns`; single panel otherwise (backward compatible)

- [ ] **Step 1: Add chart test**

Append to `tests/test_credit_spreads.py`:

```python
def test_make_chart_creates_file_single_panel():
    import matplotlib
    matplotlib.use("Agg")
    from tools.credit_spreads import make_chart
    df = make_mock_df(("HY",))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "chart.png"
        make_chart(df, ["HY"], pd.Series(dtype=float), out)
        assert out.exists() and out.stat().st_size > 0


def test_make_chart_creates_file_two_panel():
    import matplotlib
    matplotlib.use("Agg")
    from tools.credit_spreads import make_chart
    df = make_mock_df(("HY", "IG"))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "chart.png"
        make_chart(df, ["HY", "IG"], pd.Series(dtype=float), out)
        assert out.exists() and out.stat().st_size > 0
```

- [ ] **Step 2: Run new tests to confirm they fail**

```
pytest tests/test_credit_spreads.py::test_make_chart_creates_file_single_panel tests/test_credit_spreads.py::test_make_chart_creates_file_two_panel -v
```

Expected: Both fail — `make_chart` doesn't exist with the new behavior yet. (They may actually pass since the function exists — that's fine; move on to the implementation.)

- [ ] **Step 3: Replace `make_chart()` in `tools/credit_spreads.py`**

Replace the entire `make_chart` function with:

```python
def make_chart(
    df: pd.DataFrame,
    series_keys: list[str],
    recessions: pd.Series,
    out_path: Path,
) -> None:
    BG = "#0a0f1e"
    GRID = "#1e2a3a"

    has_diff = "HY" in df.columns and "IG" in df.columns

    if has_diff:
        fig, (ax, ax_diff) = plt.subplots(
            2, 1, figsize=(14, 9), dpi=150,
            gridspec_kw={"height_ratios": [3, 1], "hspace": 0.06},
        )
    else:
        fig, ax = plt.subplots(figsize=(14, 7), dpi=150)
        ax_diff = None

    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # Recession shading (top panel only)
    drew_recession = False
    if not recessions.empty:
        in_rec = False
        rec_start = None
        chart_start = df.index[0]
        chart_end   = df.index[-1]
        for date, val in recessions.items():
            if val == 1 and not in_rec:
                rec_start = date
                in_rec = True
            elif val == 0 and in_rec:
                if rec_start <= chart_end and date >= chart_start:
                    ax.axvspan(
                        max(rec_start, chart_start), min(date, chart_end),
                        color="#c0392b", alpha=0.15, zorder=0,
                    )
                    drew_recession = True
                in_rec = False
        if in_rec and rec_start is not None:
            if rec_start <= chart_end:
                ax.axvspan(
                    max(rec_start, chart_start), chart_end,
                    color="#c0392b", alpha=0.15, zorder=0,
                )
                drew_recession = True

    # Series lines
    for key in series_keys:
        if key not in df.columns:
            continue
        s = df[key].dropna()
        color = SERIES_COLORS.get(key, "#ffffff")
        _, label = SERIES_MAP[key]
        ax.plot(s.index, s.values, color=color, lw=1.8, label=label, zorder=3)
        ax.scatter([s.index[-1]], [s.iloc[-1]], color=color, s=40, zorder=4)
        ax.annotate(
            f"{s.iloc[-1]:.2f}%",
            xy=(s.index[-1], s.iloc[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            color=color,
            fontsize=9,
            fontweight="bold",
            va="center",
        )

    # Top panel styling
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors="#8899aa", labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.grid(True, color=GRID, linewidth=0.6, linestyle="--", alpha=0.7)
    ax.set_xlim(df.index[0], df.index[-1])
    if ax_diff is not None:
        ax.tick_params(labelbottom=False)  # hide x-axis labels on top panel

    # Legend
    handles, labels = ax.get_legend_handles_labels()
    if drew_recession:
        rec_patch = plt.Rectangle((0, 0), 1, 1, fc="#c0392b", alpha=0.3)
        handles.append(rec_patch)
        labels.append("NBER Recession")
    ax.legend(handles, labels, framealpha=0.15, edgecolor=GRID,
              labelcolor="#cccccc", fontsize=9, loc="upper left")

    # Title
    now = datetime.now().strftime("%Y-%m-%d")
    ax.set_title(
        f"Credit Spread History  —  {now}",
        color="#e8e8e8", fontsize=13, fontweight="bold", pad=14,
    )
    ax.set_ylabel("Option-Adjusted Spread (%)", color="#8899aa", fontsize=9)

    # Bottom panel — differential
    if ax_diff is not None:
        ax_diff.set_facecolor(BG)
        hy = df["HY"].dropna()
        ig = df["IG"].dropna()
        common = hy.index.intersection(ig.index)
        diff = hy.loc[common] - ig.loc[common]

        ax_diff.plot(diff.index, diff.values, color="#aaaaaa", lw=1.5)
        median_val = diff.median()
        ax_diff.axhline(median_val, color="#aaaaaa", lw=0.8, linestyle="--", alpha=0.6)
        ax_diff.annotate(
            f"Median {median_val:.2f}%",
            xy=(diff.index[-1], median_val),
            xytext=(8, 4),
            textcoords="offset points",
            color="#aaaaaa",
            fontsize=8,
            va="bottom",
        )

        for spine in ax_diff.spines.values():
            spine.set_color(GRID)
        ax_diff.tick_params(colors="#8899aa", labelsize=8)
        ax_diff.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
        ax_diff.grid(True, color=GRID, linewidth=0.6, linestyle="--", alpha=0.7)
        ax_diff.set_ylabel("HY–IG (%)", color="#8899aa", fontsize=8)
        ax_diff.set_xlim(df.index[0], df.index[-1])

    fig.tight_layout(pad=1.2)
    TMP.mkdir(exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG, edgecolor="none")
    plt.close()
    print(f"  Chart -> {out_path}")
```

- [ ] **Step 4: Run all tests**

```
pytest tests/test_credit_spreads.py -v
```

Expected: all 6 tests pass.

- [ ] **Step 5: Commit**

```
git add tools/credit_spreads.py tests/test_credit_spreads.py
git commit -m "feat: split credit spread chart into two panels with HY-IG differential below"
```

---

## Task 3: `make_stack_chart()` + wire into `main()`

**Files:**
- Modify: `tools/credit_spreads.py` — add `make_stack_chart()`, update `main()`

**Interfaces:**
- Consumes: `make_stack_chart(df, series_keys, recessions, out_path)` — same signature pattern as `make_chart()`
- Produces: PNG at `out_path`; `main()` calls it automatically when `--chart` is used and HY+IG are both in the fetched df

- [ ] **Step 1: Add stack chart test**

Append to `tests/test_credit_spreads.py`:

```python
def test_make_stack_chart_creates_file():
    import matplotlib
    matplotlib.use("Agg")
    from tools.credit_spreads import make_stack_chart
    df = make_mock_df(("HY", "IG", "CCC"))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "stack.png"
        make_stack_chart(df, ["HY", "IG", "CCC"], pd.Series(dtype=float), out)
        assert out.exists() and out.stat().st_size > 0


def test_make_stack_chart_hy_ig_only():
    import matplotlib
    matplotlib.use("Agg")
    from tools.credit_spreads import make_stack_chart
    df = make_mock_df(("HY", "IG"))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "stack.png"
        make_stack_chart(df, ["HY", "IG"], pd.Series(dtype=float), out)
        assert out.exists() and out.stat().st_size > 0
```

- [ ] **Step 2: Run new tests to confirm they fail**

```
pytest tests/test_credit_spreads.py::test_make_stack_chart_creates_file tests/test_credit_spreads.py::test_make_stack_chart_hy_ig_only -v
```

Expected: ImportError — `make_stack_chart` not defined yet.

- [ ] **Step 3: Add `make_stack_chart()` to `tools/credit_spreads.py`**

Add this function after `make_chart()` and before `main()`. Also add `from matplotlib.patches import Patch` at the top of the function (not as a module-level import):

```python
def make_stack_chart(
    df: pd.DataFrame,
    series_keys: list[str],
    recessions: pd.Series,
    out_path: Path,
) -> None:
    from matplotlib.patches import Patch

    BG = "#0a0f1e"
    GRID = "#1e2a3a"

    fig, ax = plt.subplots(figsize=(14, 7), dpi=150)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # Align all available series to a common date index
    hy  = df["HY"].dropna()  if "HY"  in df.columns else None
    ig  = df["IG"].dropna()  if "IG"  in df.columns else None
    ccc = df["CCC"].dropna() if "CCC" in df.columns else None

    idx = ig.index
    if hy is not None:
        idx = idx.intersection(hy.index)
    if ccc is not None:
        idx = idx.intersection(ccc.index)

    ig_vals  = ig.loc[idx].values
    hy_vals  = hy.loc[idx].values  if hy  is not None else None
    ccc_vals = ccc.loc[idx].values if ccc is not None else None
    zeros    = np.zeros(len(idx))

    # Recession shading
    if not recessions.empty:
        in_rec    = False
        rec_start = None
        chart_start = idx[0]
        chart_end   = idx[-1]
        for date, val in recessions.items():
            if val == 1 and not in_rec:
                rec_start = date
                in_rec = True
            elif val == 0 and in_rec:
                if rec_start <= chart_end and date >= chart_start:
                    ax.axvspan(
                        max(rec_start, chart_start), min(date, chart_end),
                        color="#c0392b", alpha=0.12, zorder=0,
                    )
                in_rec = False
        if in_rec and rec_start is not None and rec_start <= chart_end:
            ax.axvspan(max(rec_start, chart_start), chart_end,
                       color="#c0392b", alpha=0.12, zorder=0)

    # Layer 1: IG base (0 → IG)
    ax.fill_between(idx, zeros, ig_vals, color="#4a9eff", alpha=0.5, zorder=1)
    ax.plot(idx, ig_vals, color="#4a9eff", lw=1.2, zorder=2)

    # Layer 2: HY–IG quality premium (IG → HY)
    if hy_vals is not None:
        ax.fill_between(idx, ig_vals, hy_vals, color="#f5a623", alpha=0.5, zorder=1)
        ax.plot(idx, hy_vals, color="#f5a623", lw=1.2, zorder=2)

    # Layer 3: CCC premium (HY → CCC)
    if ccc_vals is not None and hy_vals is not None:
        ax.fill_between(idx, hy_vals, ccc_vals, color="#e05c5c", alpha=0.5, zorder=1)
        ax.plot(idx, ccc_vals, color="#e05c5c", lw=1.2, zorder=2)

    # Right-edge annotations
    last = idx[-1]
    ig_last = ig_vals[-1]
    ax.annotate(
        f"IG {ig_last:.2f}%",
        xy=(last, ig_last / 2),
        xytext=(10, 0), textcoords="offset points",
        color="#4a9eff", fontsize=9, fontweight="bold", va="center",
    )
    if hy_vals is not None:
        hy_last   = hy_vals[-1]
        prem_last = hy_last - ig_last
        ax.annotate(
            f"Quality Premium {prem_last:.2f}%",
            xy=(last, ig_last + prem_last / 2),
            xytext=(10, 0), textcoords="offset points",
            color="#f5a623", fontsize=9, fontweight="bold", va="center",
        )
        if ccc_vals is not None:
            ccc_last     = ccc_vals[-1]
            ccc_prem_last = ccc_last - hy_last
            ax.annotate(
                f"CCC Premium {ccc_prem_last:.2f}%",
                xy=(last, hy_last + ccc_prem_last / 2),
                xytext=(10, 0), textcoords="offset points",
                color="#e05c5c", fontsize=9, fontweight="bold", va="center",
            )

    # Styling
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors="#8899aa", labelsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.grid(True, color=GRID, linewidth=0.6, linestyle="--", alpha=0.7)
    ax.set_xlim(idx[0], idx[-1])
    ax.set_ylabel("Option-Adjusted Spread (%)", color="#8899aa", fontsize=9)

    now = datetime.now().strftime("%Y-%m-%d")
    ax.set_title(
        f"Credit Spread Stack  —  {now}",
        color="#e8e8e8", fontsize=13, fontweight="bold", pad=14,
    )

    legend_elements = [
        Patch(facecolor="#4a9eff", alpha=0.7, label="IG Base"),
        Patch(facecolor="#f5a623", alpha=0.7, label="HY–IG Quality Premium"),
    ]
    if ccc_vals is not None:
        legend_elements.append(Patch(facecolor="#e05c5c", alpha=0.7, label="CCC Premium"))
    if not recessions.empty:
        legend_elements.append(Patch(facecolor="#c0392b", alpha=0.3, label="NBER Recession"))
    ax.legend(handles=legend_elements, framealpha=0.15, edgecolor=GRID,
              labelcolor="#cccccc", fontsize=9, loc="upper left")

    fig.tight_layout(pad=1.2)
    TMP.mkdir(exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG, edgecolor="none")
    plt.close()
    print(f"  Stack chart -> {out_path}")
```

- [ ] **Step 4: Wire `make_stack_chart()` into `main()`**

Find the existing `if args.chart:` block in `main()`:

```python
    if args.chart:
        print("Fetching recession data...")
        recessions = fetch_recessions(args.start)
        today = datetime.now().strftime("%Y%m%d")
        out = TMP / f"credit_spreads_{today}.png"
        make_chart(df, args.series, recessions, out)
```

Replace with:

```python
    if args.chart:
        print("Fetching recession data...")
        recessions = fetch_recessions(args.start)
        today = datetime.now().strftime("%Y%m%d")
        out = TMP / f"credit_spreads_{today}.png"
        make_chart(df, args.series, recessions, out)
        if "HY" in df.columns and "IG" in df.columns:
            stack_out = TMP / f"credit_spreads_stack_{today}.png"
            make_stack_chart(df, args.series, recessions, stack_out)
```

- [ ] **Step 5: Run all tests**

```
pytest tests/test_credit_spreads.py -v
```

Expected: all 8 tests pass.

- [ ] **Step 6: Run the CLI end-to-end and inspect both output charts**

```
python tools/credit_spreads.py --series HY IG CCC --chart
```

Expected terminal output:
```
Fetching credit spread data from FRED...
  OK  BAMLH0A0HYM2           US High Yield OAS  (N obs)
  OK  BAMLC0A0CM             US Investment Grade OAS  (N obs)
  OK  BAMLH0A3HYC            US CCC-Rated OAS  (N obs)

Credit Spread Snapshot  —  2026-06-21
====================================================================
  Series                      Current   52W Low  52W High   Pctile   WoW Chg
--------------------------------------------------------------------
  US High Yield OAS             X.XX%    ...
  US Investment Grade OAS       X.XX%    ...
  US CCC-Rated OAS              X.XX%    ...
--------------------------------------------------------------------
  HY–IG Quality Premium         X.XX%    ...
====================================================================
  Source: ICE BofA via FRED  |  OAS = Option-Adjusted Spread over Treasuries

Fetching recession data...
  Chart -> .tmp/credit_spreads_20260621.png
  Stack chart -> .tmp/credit_spreads_stack_20260621.png
```

Open both PNGs and verify:
- `credit_spreads_20260621.png`: three spread lines on top panel, differential line on bottom panel with median reference
- `credit_spreads_stack_20260621.png`: three stacked filled areas (blue base, orange premium band, red CCC band) with recession shading and right-edge labels

- [ ] **Step 7: Commit**

```
git add tools/credit_spreads.py tests/test_credit_spreads.py
git commit -m "feat: add tier stack chart to credit_spreads tool"
```

---

## Task 4: Write Post 16 draft

**Files:**
- Create: `drafts/post_16_spread_spectrum.md`

**Interfaces:**
- Consumes: live CLI output from Task 3 (exact numbers from terminal), both chart PNGs at `.tmp/`

- [ ] **Step 1: Run the tool and record all output**

```
python tools/credit_spreads.py --series HY IG CCC --chart
```

Copy the full terminal output (fetch lines, snapshot table including the differential row, chart paths). You will paste this verbatim into the post.

- [ ] **Step 2: Note the exact values for the interpretation section**

From the output, record:
- HY OAS current, percentile rank, WoW change
- IG OAS current, percentile rank, WoW change
- CCC OAS current, percentile rank, WoW change
- HY–IG Quality Premium current, percentile rank
- Today's date (YYYY-MM-DD)
- Chart filenames (for image embed paths)

- [ ] **Step 3: Write `drafts/post_16_spread_spectrum.md`**

Use the structure below. Fill in `[LIVE: ...]` placeholders with exact values from Step 2.

```markdown
# The Spread Spectrum: IG, HY, and Distressed

*DeltaTheta | Post 16 of the Build Series*

*Written by Claude with oversight.*

The number from last week — HY OAS at [LIVE: current HY]% — is an aggregate. One number for hundreds of bonds across dozens of industries. Underneath it are three quality tiers, each pricing a different kind of risk, each moving on a different clock. The tier you look at determines what the signal means. The gap between tiers is a signal in its own right.

---

## Three Tiers, Three Risk Layers

Not all corporate bonds are the same credit risk. The ICE BofA indices split the market into quality buckets, each with its own spread dynamic:

| Tier | Rating | Typical Calm Range | Typical Stress Range | What Drives It |
|------|--------|-------------------|---------------------|----------------|
| Investment Grade (IG) | BBB and above | 50–150bps | 200–400bps | Liquidity risk, macro rate environment |
| High Yield (HY) | BB and below | 250–500bps | 800–2000bps | Default risk + macro |
| CCC / Distressed | CCC and below | 700–1200bps | 1500–3000bps+ | Near-term restructuring probability |

**Investment Grade** is the large-cap universe — household names with investment-grade ratings and reliable access to capital markets. When IG spreads widen, it's a systemic signal: something is wrong with the whole system, not just the weak players. IG was at ~360bps in 2008 and ~280bps in March 2020 — both recessions. It's relatively quiet in normal times.

**High Yield** is the leveraged layer — companies running thinner coverage ratios that need cheap capital to operate. HY is more volatile than IG because the margin for error is smaller. Spreads here move first when credit conditions tighten and recover first when they ease. This is the tier professional credit analysts watch most closely as a leading indicator.

**CCC** is the distressed end. When CCC spreads break above ~1000bps, the market is pricing near-certain restructuring for a meaningful slice of the index. This tier doesn't lead — it confirms. By the time CCC blows out, the stress event is already underway. It's a severity gauge.

---

## The Quality Premium

The spread between HY and IG — the quality premium — is its own signal, separate from where each tier trades in absolute terms.

When the premium is **compressed**, the market isn't asking hard questions about credit quality. Capital flows to strong and weak borrowers alike at nearly the same relative cost. This can mean genuine confidence — or it can mean the pricing mechanism has been distorted by duration-chasing and risk-appetite overhang.

When the premium **widens**, discrimination is underway. Weak borrowers are being re-priced specifically, while stronger issuers hold relatively steady. This often precedes broader spread widening by weeks to months.

---

## The Tool

`tools/credit_spreads.py` now tracks all three tiers and computes the quality premium automatically.

```
python tools/credit_spreads.py --series HY IG CCC --chart
```

One command produces the snapshot table plus two charts: the time-series with differential panel, and a new tier stack chart showing the spread hierarchy as layered regions.

---

## Today's Reading

```
python tools/credit_spreads.py --series HY IG CCC --chart

[LIVE: paste full terminal output here]
```

![Credit Spread History — HY, IG, CCC](../.tmp/[LIVE: credit_spreads_YYYYMMDD.png])

![Credit Spread Stack — Tier Hierarchy](../.tmp/[LIVE: credit_spreads_stack_YYYYMMDD.png])

---

## What This Is Saying

[LIVE: Write this section using actual numbers from the tool output. Cover three points:]

**All three tiers at or near historical lows.** [HY at X% (Nth percentile), IG at X% (Nth percentile), CCC at X% (Nth percentile). Note whether this is broad-based or tier-specific.]

**Quality premium compressed.** [HY–IG at X% (Nth percentile). What this implies about how the market is differentiating — or not — between credit quality tiers.]

**Direction.** [Week-over-week changes across tiers. Is the move consistent across the stack or is one tier diverging?]

Two reads:

**The constructive read:** [Fill in with current context — if spreads are tight because capital is abundant and default rates are genuinely low, say so concretely.]

**The skeptical read:** [Quality premia that compress this far historically precede repricing. When the tide turns, the move from current levels could be sharp precisely because there's so little risk premium to absorb it. Use the specific percentile numbers to make this concrete.]

No position taken. The pipeline reads; the reader decides.

---

## Next: Credit as a Leading Indicator

The next post turns this into a cross-asset signal. We'll look at the historical relationship between credit spreads and equity — whether spread moves lead or lag equity turns, what the historical case studies show, and what the current configuration implies for equity direction over the next several months.

---

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

*← [Post 15: OAS 101](#) | [Post 17: Credit vs Equity →](#)*

— *DeltaTheta*
```

- [ ] **Step 4: Replace all `[LIVE: ...]` placeholders with actual values**

Go through every placeholder and substitute the real number or text. There should be zero `[LIVE:` strings remaining when done.

- [ ] **Step 5: Verify the post**

Check:
- Image paths match actual filenames in `.tmp/`
- All three tiers have concrete numbers in the interpretation section
- Quality premium row is referenced explicitly
- Two reads are written with specific numbers, not vague language
- Tease for post 17 is present
- BMC button is present
- Series navigation footer is present: `← Post 15: OAS 101 | Post 17: Credit vs Equity →`
- No `[LIVE:` strings remain

- [ ] **Step 6: Commit**

```
git add drafts/post_16_spread_spectrum.md
git commit -m "feat: add post 16 draft — spread spectrum"
```
