# Design: Correlation Map — Post #12

**Date:** 2026-06-17
**Post:** `drafts/post_12_correlation_map.md`
**Script:** `tools/correlation_matrix.py`

---

## Objective

Build a generic, reusable correlation matrix tool and a Substack post showing how macro asset proxies are moving together right now — and what changed in the last week.

---

## Deliverables

1. `tools/correlation_matrix.py` — standalone CLI script
2. `.tmp/correlation_matrix_<date>.png` — 3-panel heatmap figure
3. `drafts/post_12_correlation_map.md` — Substack post draft
4. `workflows/correlation_matrix.md` — SOP for running this tool

---

## Script Design (`tools/correlation_matrix.py`)

### Pattern
Standalone. No imports from other `tools/` scripts. Uses `yfinance` for price data directly, same SSL/session setup as `price_fetch.py`.

### CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--tickers` | `SPY IWM QQQ TLT IEF GLD DX-Y.NYB` | Space-separated Yahoo Finance ticker symbols |
| `--window` | `63` | Lookback in trading days for each correlation snapshot |
| `--prior-offset` | `5` | Trading days to shift the "prior" window back (5 = 1 week) |
| `--lookback-days` | `400` | Total days of price history to fetch (must be > window + prior-offset + buffer) |
| `--start` | `None` | Optional explicit start date (YYYY-MM-DD); overrides `--lookback-days` |
| `--end` | `None` | Optional explicit end date (YYYY-MM-DD); defaults to today |
| `--labels` | `None` | Display name overrides as `TICKER:LABEL` pairs, e.g. `DX-Y.NYB:DXY IEF:10Y` |
| `--out` | `.tmp/correlation_matrix_<YYYYMMDD>.png` | Output PNG path |

### Default Ticker Set and Macro Proxy Mapping

| Ticker | Yahoo Symbol | Macro Factor |
|---|---|---|
| SPY | SPY | US equities (S&P 500) |
| IWM | IWM | Risk appetite / small caps (Russell 2000) |
| QQQ | QQQ | Growth / tech (Nasdaq 100) |
| TLT | TLT | Long-duration rates (20Y+ Treasuries) |
| IEF | IEF | 10Y note proxy (7–10Y Treasuries) |
| GLD | GLD | Gold / real assets / fear |
| DXY | DX-Y.NYB | US dollar strength |

### Computation

1. Fetch daily adjusted close prices for all tickers over `--lookback-days` ending `--end`
2. Compute daily log returns: `log(close / close.shift(1))`
3. Slice two windows from the returns series:
   - **Current:** last `window` trading days ending `end`
   - **Prior:** `window` trading days ending `end - prior_offset` trading days
4. Compute Pearson correlation matrix for each window
5. Compute delta matrix: `current - prior`

### Output

**Figure:** Single `matplotlib` figure, 3 panels side by side, saved as PNG.

- **Panel 1 — Current** (63d ending today)
  - Diverging colormap (`RdBu_r`), range `[-1, 1]`
  - Diagonal masked (NaN / white)
  - Cell values annotated (2 decimal places)
- **Panel 2 — Prior** (63d ending 5 days ago)
  - Same colormap and scale as Panel 1
- **Panel 3 — Delta** (current minus prior)
  - Separate diverging colormap centered at 0 (`RdYlGn`), range `[-0.5, 0.5]`
  - Values annotated with `+0.12` / `-0.08` sign formatting
  - Largest absolute changes visually pop

Figure suptitle stamps both date windows, e.g.:
`"63-Day Correlation Snapshot  |  Current: Mar 20 – Jun 17, 2026  vs  Prior: Mar 13 – Jun 10, 2026"`

**Stdout:** Ranked list of top 5 pairs by absolute delta, e.g.:
```
Top movers (current vs prior):
  SPY / TLT    -0.31 → -0.12  (+0.19)
  QQQ / DXY   +0.18 → +0.04  (-0.14)
  ...
```

---

## Post Design (`drafts/post_12_correlation_map.md`)

### Title
*"The Correlation Map: How Macro Assets Are Moving Together Right Now"*

### Series line
*DeltaTheta | Post 12 of the Build Series*

### Structure

1. **Lede** — Why correlations matter more than individual asset views. The "flight to safety" trade only works if the bonds-equity correlation is actually negative. Regime shifts show up in correlations before they show up in price trends.

2. **The proxy map** — Brief explanation of what each ticker represents as a macro factor (table format).

3. **The tool** — CLI command with actual terminal output (per post convention — post is the documentation).

4. **Current snapshot** — Embed the 3-panel PNG. Then 2–3 paragraphs reading the delta: which relationships shifted, what that could mean for the current regime.

5. **Bottom line** — One-paragraph synthesis of the current correlation regime.

6. **BMC footer** — Buy Me a Coffee embed (slug: DeltanTheta).

> **Note:** The "reading the chart" narrative section is written *after* running the script and seeing actual output. The post follows the data.

---

## Workflow (`workflows/correlation_matrix.md`)

Documents:
- Purpose and when to run
- Full CLI reference
- How to interpret the delta heatmap
- Ticker add/remove instructions (the script is generic — just change `--tickers`)
- Known quirks (yfinance SSL workaround, DX-Y.NYB as DXY proxy)

---

## Future Extensibility

The script is designed for easy ticker changes going forward:
- Add/remove tickers via `--tickers` at call time — no code changes needed
- `--labels` handles display name cleanup for any ticker with a cryptic Yahoo symbol
- `--window` and `--prior-offset` are both runtime arguments — can compare 21d vs 63d, or 1-month vs 3-month prior
- Output is a single self-contained PNG — works in Substack, X, Reddit posts unchanged
