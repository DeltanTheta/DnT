# Credit Spreads Series — Design Spec

**Date:** 2026-06-20
**Series:** Posts 14–18 (DeltaTheta Build Series)
**Status:** Approved

---

## Overview

A five-post series on credit spreads, structured as one scene-setting intro followed by a four-post technical build arc. The series adds the final major pillar to the macro pipeline: credit market stress. After this series, the next chapter will be money flows.

The reader target is investors and portfolio managers who understand macro broadly but may not have a rigorous credit framework. Each post introduces a concept, builds a tool, and shows a live reading — consistent with the build-series format established in posts 1–13.

---

## Macro Context (runs through all five posts)

These themes provide the "why now" backdrop. Weave them in where relevant rather than front-loading them all in post 14.

- **Sovereign debt at peacetime records** — debt-to-GDP levels across developed markets constrain policy options and shift the baseline for what "normal" spreads mean
- **Fed leadership transition** — probable new chair with a more dovish mandate; political pressure for lower rates colliding with fiscal reality
- **Trump rate pressure** — executive desire for lower rates creates tension with credit market pricing of risk
- **USD stablecoins and Treasury demand** — emerging stablecoin legislation could structurally reshape who buys U.S. Treasuries and at what price, with downstream effects on credit spread floors

---

## Post Structure

### Post 14 — Series Intro: "The Missing Piece"
*No new tool. Pure context and framing.*

**Objective:** Earn the reader's attention before asking them to spend four posts on credit mechanics. Connect what the pipeline has already built to why credit is the logical next step.

**Structure:**
1. **The pipeline so far** — brief recap of what exists: yield curve, employment, GDP, inflation, vol regime (VIX + term structure), correlation matrix, sector money flow. Frame it as a real-time machine for reading macro conditions. One major pillar missing.
2. **Why credit** — equities price expected earnings; credit prices the probability of not getting paid back. Spreads widen before equity breaks. They compress before rallies sustain. For institutional PMs, credit is a primary risk signal, not secondary.
3. **Why now** — the macro backdrop (sovereign debt, Fed transition, rate politics, stablecoin/Treasury). These tensions don't resolve cleanly — credit spreads are where they'll show up first.
4. **Series tease** — four posts over the coming days:
   - Post 15: What OAS is and what the pipeline now tracks
   - Post 16: The spread spectrum — IG vs HY vs distressed
   - Post 17: Credit as a leading indicator — what it says about equity
   - Post 18: The regime framework — levels, triggers, and what to watch
5. **Money flows forward reference** (if post runs short): "After this series we'll build out the money flow framework — tracking where capital is actually moving and what that predicts for relative asset performance."
6. **BMC button**

---

### Post 15 — OAS 101
*Introduces `tools/credit_spreads.py`*

**Objective:** Explain exactly what option-adjusted spread is and build the pipeline tool that tracks it.

**Concepts:**
- What a spread is: yield premium over a risk-free benchmark
- Why "option-adjusted": callable bond mechanics, stripping out the embedded option so you're comparing apples to apples
- FRED series map:
  - `BAMLH0A0HYM2` — ICE BofA US High Yield OAS (primary series)
  - `BAMLC0A0CM` — ICE BofA US Corporate (IG) OAS
  - `BAMLH0A0HYM2EY` — HY Effective Yield
  - `BAMLC0A0CMEY` — IG Effective Yield

**Tool:** `tools/credit_spreads.py`
- Fetches HY OAS and IG OAS from FRED via `fred_fetch.py` or directly via FRED API
- Outputs: current reading, 52-week range, percentile rank, week-over-week change
- CLI: `python tools/credit_spreads.py` with optional `--series`, `--start`, `--chart` flags

**Live reading:** Current HY OAS snapshot with context.

**Money flows tease** (if space): forward reference to next series.

**BMC button**

---

### Post 16 — The Spread Spectrum
*Extends `tools/credit_spreads.py` or uses existing tool with new flags*

**Objective:** Show that credit is not monolithic — different tiers price different layers of risk.

**Concepts:**
- Investment grade (IG): large, stable issuers; spreads reflect macro rate and liquidity risk
- High yield (HY): leveraged issuers; spreads reflect idiosyncratic default risk + macro
- Distressed: spreads >1000bps; pricing near-certain restructuring
- The compression/widening cycle: where each tier leads the other in stress events

**Data additions:**
- CCC-rated tier if available on FRED (`BAMLH0A3HYC`)
- IG–HY spread differential as its own signal

**Live reading:** Where each tier sits today vs historical norms. What the current tier hierarchy implies.

**Money flows tease** (if space).

**BMC button**

---

### Post 17 — Credit vs Equity
*Analysis post — no new tool required*

**Objective:** Show credit as a leading indicator. Historical case studies + current divergence/convergence read.

**Concepts:**
- Why credit leads equity: credit holders price downside first; equity holders price upside
- Historical divergences: 2007 (HY widened months before SPX topped), 2019 (spreads compressed, equity followed), 2022 (simultaneous — unusual)
- The Leuthold "credit vs equity stress" framework as a reference point

**Analysis:**
- Overlay HY OAS vs SPX returns (lagged correlation)
- Current relationship: are spreads and equity telling the same story or diverging?
- What the current read implies for equity direction over the next 3–6 months

**Money flows tease** (if space).

**BMC button**

---

### Post 18 — The Regime Framework
*Synthesis post — no new tool; pulls together all five macro pillars*

**Objective:** Give investors and PMs a practical forward framework: specific levels, triggers, and context for reading credit in the current macro environment.

**Concepts:**
- Tight vs wide regimes: what historical median, 75th pct, and 90th pct OAS levels have meant
- Recession signal thresholds: the spread levels that have historically preceded contractions
- How the macro backdrop shifts the baseline: sovereign debt levels mean "normal" today may be structurally wider than 2010–2019 norms

**Framework output:**
- A simple regime table: Green / Yellow / Red by spread level and trend direction
- Current regime placement
- What to watch in the coming months: specific FRED series and levels

**Series close:**
- Tease the money flows series: "The next chapter builds on this — we'll track where capital is actually moving across asset classes and what that predicts for relative performance."

**BMC button**

---

## Tool Spec: `tools/credit_spreads.py`

**Data source:** FRED API (via existing `.env` FRED_API_KEY)

**Primary series:**
| FRED ID | Description |
|---------|-------------|
| BAMLH0A0HYM2 | US HY OAS (ICE BofA) |
| BAMLC0A0CM | US IG OAS (ICE BofA) |
| BAMLH0A3HYC | US CCC OAS (ICE BofA) |
| BAMLH0A0HYM2EY | US HY Effective Yield |
| BAMLC0A0CMEY | US IG Effective Yield |

**CLI flags:**
- `--series` — which spread(s) to fetch (default: HY + IG)
- `--start` — lookback start date (default: 5 years)
- `--chart` — output PNG chart to `.tmp/`

**Outputs:**
- Table: current OAS, 52-week high/low, percentile rank, WoW change
- Optional: time-series chart with recession shading (FRED USREC)

**Reuse:** `fred_fetch.py` for the FRED API calls; `credit_spreads.py` adds the spread-specific logic, percentile ranking, and chart output.

---

## Series-Level Conventions

- All posts tagged as part of the credit spreads series (Substack series feature if available)
- Consistent opening recap: "In this series we're building a credit spread framework from scratch."
- Consistent closing: BMC button, series navigation (← previous | next →)
- Money flows forward reference available as filler in any post that runs short

---

## What Comes After

**Next series: Money Flows**
- How capital moves across asset classes
- What flow data predicts for relative performance
- Tools TBD (likely extends `sector_money_flow.py`, adds cross-asset flow analysis)
