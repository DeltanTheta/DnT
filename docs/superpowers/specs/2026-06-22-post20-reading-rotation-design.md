# Post 20: Reading Rotation — Design Spec

**Date:** 2026-06-22
**Series:** Money Flows (Posts 19–21)
**Status:** Approved

---

## Objective

Build `tools/flow_trend.py` and draft Post 20: "Reading Rotation." The post extends the Post 19 snapshot into a time-series view — showing how the current CMF rankings got to where they are over the past 60–90 days, and where that places us in the classic sector rotation sequence.

---

## Tool: `tools/flow_trend.py`

### Source data

Reads the latest `.tmp/capital_flows_*.csv` produced by `capital_flows.py`. The CSV already contains date-indexed 30-day CMF values for all 13 tickers — no new data fetch needed.

### Output

A single 3-panel stacked PNG saved to `.tmp/flow_trend_<date>.png`. Each panel plots 30-day CMF over time as multi-line chart.

**Panel groupings:**

| Panel | Label | Tickers |
|-------|-------|---------|
| Top | Cyclicals | XLE, XLI, XLB, XLY, XLK |
| Middle | Defensives | XLP, XLU, XLV, XLRE, XLC |
| Bottom | Macro Proxies | XLF, TLT, GLD |

**Per panel:**
- X-axis: dates (last `--lookback` trading days, default 60)
- Y-axis: 30-day CMF, range clipped to ±0.5
- Horizontal zero line for reference
- One colored line per ticker, labeled in legend
- Consistent color assignments across runs (fixed color map per ticker)

### CLI

```
python tools/flow_trend.py                          # 60-day lookback, latest CSV
python tools/flow_trend.py --lookback 90            # override lookback window
python tools/flow_trend.py --csv .tmp/capital_flows_20260622.csv  # specify CSV
python tools/flow_trend.py --out .tmp/myfile.png    # override output path
```

### Implementation notes

- Find latest CSV by globbing `.tmp/capital_flows_*.csv`, sort by filename, take last
- Column naming in CSV: `XLK_cmf30`, `XLF_cmf30`, etc. (from `capital_flows.py` save format)
- Slice to last N rows by index (trading days, not calendar days)
- Use `matplotlib` subplots with shared x-axis (`sharex=True`)
- Apply `tight_layout()` with adequate padding to avoid label overlap
- Do not import or depend on `capital_flows.py` — read the CSV directly

### File outputs

| File | Description |
|------|-------------|
| `tools/flow_trend.py` | New standalone tool |
| `.tmp/flow_trend_<date>.png` | 3-panel trend chart |

---

## Post 20: Reading Rotation

### Structure

1. **Bridge from Post 19** — the snapshot shows where flow stands today. This post shows how it got there. One paragraph.

2. **Rotation primer** — 2–3 paragraphs covering the classic sector rotation sequence (expansion → peak → contraction → recovery). Not exhaustive — enough context to make the chart readable. Connect CMF trending up/down to capital moving into/out of a phase.

3. **The tool + CLI** — commands and terminal output per established series convention. Chart embedded immediately after.

4. **Reading the three panels** — interpret each group:
   - Cyclicals: which are trending up vs rolling over; phase signal
   - Defensives: whether defensives are gaining relative to cyclicals (late cycle signal)
   - Macro proxies: XLF trend (credit/risk appetite), TLT trend (rate expectations), GLD trend (inflation hedge / risk-off demand)

5. **Forward signal** — one clear "what to watch" per panel. What would confirm the current rotation thesis or invalidate it.

6. **BMC footer**, no paywall. Full post free.

### Conventions

- CLI commands + actual terminal output embedded (no inline `#` comments — cmd.exe incompatible)
- Chart embedded in draft as `.tmp/` relative path in markdown (base64 conversion handled by `substack_post.py` at publish time)
- Navigation footer: `← Post 19: The Flow Lens | Post 21: Divergence Signals →`
- Byline: *Written by Claude with oversight.*

---

## Constraints

- `flow_trend.py` reads from existing CSV only — no new yfinance calls, no new API keys
- Do not modify `capital_flows.py`
- No paywall
- Post must include actual CLI output from a real tool run
