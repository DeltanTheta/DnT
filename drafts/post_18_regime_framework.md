# The Regime Framework: Levels, Triggers, and What to Watch

*DeltaTheta | Post 18 of the Build Series*

*Written by Claude with oversight.*

Four posts. One concept per post: what OAS is, how the quality tiers differ, how credit leads equity. Now the close — a practical framework for putting those concepts to use. Specific levels. Specific triggers. A clear picture of where we are and what would change it.

---

## Why Regimes Rather Than Levels

A single spread reading in isolation tells you a price. A regime tells you what that price means in context.

HY OAS at 400bps means something different depending on which direction it's moving, where it's been for the past six months, what the macro backdrop looks like, and whether the move is broad-based across quality tiers or isolated in one segment. A number without trajectory and context is a map coordinate without a destination.

Regime thinking converts a continuous spread reading into a discrete state: tight (credit supportive), neutral (watch and wait), stressed (manage risk), or dislocated (damage control). Each state has a different implication for how much credit risk to carry, how to read equity signals, and how much attention to pay to spread movements.

The regimes below are calibrated to HY OAS — the primary signal — with IG and CCC as confirmation layers. None of this is mechanical. The table tells you where you are; you still have to decide what to do about it.

---

## The Framework

### HY OAS Regime Table

| Regime | HY OAS Range | Historical Context | Credit Signal | Equity Implication |
|--------|-------------|-------------------|---------------|-------------------|
| **Deep Green** | < 300bps | Near multi-year lows; rare outside extended expansions | Highly supportive | Momentum intact; limited credit headwind |
| **Green** | 300–450bps | Tight but not extreme; typical late-cycle or early-recovery | Supportive | Neutral-positive; no credit warning |
| **Yellow** | 450–600bps | Widening from tight levels or elevated plateau | Watchful | Monitor for equity lag; credit beginning to discriminate |
| **Orange** | 600–800bps | Stress event underway or cyclical trough | Stressed | Credit likely leading equity lower; reduce exposure |
| **Red** | > 800bps | Recession territory or acute dislocation | Warning | Damage control; assess recovery rates, not returns |

### Confirmation Layers

The HY OAS regime gets confirmed or questioned by two secondary signals:

**IG OAS trend:** If HY is widening and IG is holding, the stress is in the leveraged layer only — a slower-burning signal. If IG joins the widening, the stress is systemic. IG widening is a regime escalation trigger.

**CCC OAS level:** CCC above 1,200bps means a meaningful fraction of the distressed universe is pricing near-certain restructuring. CCC diverging sharply from HY (i.e., CCC elevating while HY stays tight) is an early warning — stress at the bottom of the quality stack before it spreads up. This is the signal that matters most when HY is in Deep Green.

**Quality premium (HY–IG differential):** Above 300bps, credit discrimination is underway. Below 200bps, the market has collapsed the quality distinction — historically an unstable configuration that resolves in one of two ways: the expansion continues and the compression was correct, or spreads re-price sharply when confidence breaks.

---

## The Recession Threshold

Across the modern credit history, every U.S. recession has been accompanied by HY OAS above 600bps at some point during the cycle — either in advance of the contraction, concurrent with it, or immediately following. The spread levels at key historical stress events:

| Event | HY OAS Peak | Timing |
|-------|------------|--------|
| 2001 Recession | ~1,100bps | Peaked after equity trough |
| 2008 GFC | ~2,000bps | Peaked Q4 2008, equity bottom Q1 2009 |
| 2015–2016 Energy | ~900bps | No recession; recovered within 18 months |
| 2020 COVID | ~1,100bps | Peaked March 2020; V-shaped recovery |
| 2022 Rate Shock | ~600bps | No recession declared; compressed from here |

The 600bps level is not a precise trigger — it's a zone. Sustained readings above 600bps with a widening trend have historically been associated with either an ongoing recession or a high-probability near-term contraction. A brief spike to 650bps followed by rapid compression (see: 2022) can resolve without recession.

What matters more than any single level: direction and persistence. HY at 580bps and widening is more alarming than HY at 620bps and compressing.

---

*This is where the free edition ends. What follows is the current regime placement — where we sit in the framework today — the macro caveat that complicates the reading, and the specific watch list: levels, series, and triggers for the months ahead.*

<!-- PAYWALL -->

---

## Current Regime Placement

```
python tools/credit_spreads.py --series HY IG CCC --chart

Credit Spread Snapshot  —  2026-06-21
====================================================================
  Series                      Current   52W Low  52W High   Pctile   WoW Chg
--------------------------------------------------------------------
  US High Yield OAS             2.63%     2.63%     3.46%     1.4%     -0.17
  US Investment Grade OAS       0.74%     0.73%     0.94%     1.0%     -0.01
  US CCC-Rated OAS              9.39%     7.83%    10.20%    75.0%     -0.18
--------------------------------------------------------------------
  HY-IG Quality Premium         1.89%     1.89%     2.53%     5.5%     -0.16
====================================================================
  Source: ICE BofA via FRED  |  OAS = Option-Adjusted Spread over Treasuries
```

![Credit Spread History — HY, IG, CCC](../.tmp/credit_spreads_20260621.png)

![Credit Spread Stack — Tier Hierarchy](../.tmp/credit_spreads_stack_20260621.png)

**Current regime: Deep Green — with a footnote.**

HY OAS at 2.63% sits in the Deep Green zone by every historical metric. The credit market is pricing near-zero corporate stress. IG at 0.74% confirms: systemic risk is not being priced. The quality premium at 1.89% confirms: the market is not discriminating meaningfully between strong and weak borrowers.

The footnote is CCC at the 75th percentile. The distressed tier — companies that are already under financial pressure — is not in the same zip code as IG and HY. While HY prices serenity and IG prices near-nothing, CCC prices a materially elevated probability of restructuring for the weakest segment. This bifurcation does not break the Deep Green call. But it prevents a clean, unqualified read. The market is still making some distinctions; it has just drawn the line very low on the quality ladder.

**Regime call as of June 21, 2026:** Deep Green. CCC divergence is a watch item, not a trigger.

---

## The Macro Caveat: Is This Normal?

Deep Green is historically rare. HY OAS below 300bps has occurred in only a handful of multi-year windows: the mid-2000s expansion, parts of 2014, the 2021 post-COVID reflation, and now. Each of those periods eventually resolved with spread widening — some gradual, some sharp.

But there is a structural argument that complicates the comparison. The macro backdrop today differs from prior Deep Green windows in one significant way: **sovereign debt is at peacetime records across developed markets.** Debt-to-GDP ratios that were considered emergency levels in 2010 are now baseline. Government deficits that required austerity programs in 2012 are now structural. This shifts the credit baseline.

When governments are running large structural deficits, they absorb a disproportionate share of capital markets supply. The supply of investment-grade corporate credit competes with sovereign issuance for investor dollars — but sovereigns have the advantage of (assumed) risk-free status. In that environment, corporate credit spreads may be structurally compressed relative to historical norms because the alternative (government bonds) is less attractive than it used to be when sovereign balance sheets were cleaner.

If this argument holds, the current "Deep Green" reading may be comparing today's spread to a historical baseline that no longer applies. The relevant question is not "is 2.63% historically tight?" (it is, unambiguously) but "what is the new floor?" If sovereign debt dynamics permanently shift the floor from ~300bps to ~200–250bps, then 2.63% is not as extreme as the 1st-percentile reading implies.

The pipeline does not have a method to resolve this. It's an interpretive judgment, not a quantitative one. What you should take from it: treat the percentile ranks as historical context, not as precise probability statements about today's environment.

---

## Forward Watch List

These are the specific levels and signals the pipeline is watching. They are not predictions. They are the triggers that would change the regime call.

### HY OAS Triggers

| Level | What It Means | Action |
|-------|--------------|--------|
| 3.0% (+37bps) | Minor widening from current low; still historically tight | Note the direction; no regime change |
| 3.5% (+87bps) | First yellow flag; back to mid-2025 range | Increase monitoring frequency; begin cross-asset checks |
| 4.5% (+187bps) | Entering Yellow regime | Review credit exposure; equity lag likely in 4–12 weeks |
| 5.5% (+287bps) | Yellow-to-Orange boundary | Reduce risk; credit is signaling macro stress |
| 6.5% (+387bps) | Orange-to-Red boundary | Active risk management; recession probability elevated |

### CCC OAS Triggers

| Level | What It Means |
|-------|--------------|
| 11.0% (+161bps) | Distress spreading; watch for HY lag |
| 13.0% (+361bps) | CCC entering severe stress zone; quality premium likely blowing out |
| 15.0% (+561bps) | Distressed universe pricing near-universal restructuring |

### Quality Premium (HY–IG Differential) Triggers

| Level | What It Means |
|-------|--------------|
| 2.5% (+61bps) | Credit discrimination beginning; watch for broad widening to follow |
| 3.0% (+111bps) | Clear regime signal: weak borrowers being specifically repriced |
| 3.5%+ | Stress event underway in the leveraged layer |

### FRED Series to Bookmark

```
BAMLH0A0HYM2    — US High Yield OAS (primary signal)
BAMLC0A0CM      — US Investment Grade OAS (systemic confirmation)
BAMLH0A3HYC     — US CCC OAS (early warning layer)
USREC           — NBER recession indicator (historical calibration)
BAA10Y          — Moody's BAA over 10Y Treasury (long-history proxy pre-2023)
```

The pipeline pulls all of these automatically. One command:

```
python tools/credit_spreads.py --series HY IG CCC --chart
```

---

## Closing the Credit Chapter

Five posts. One framework:

- **Post 14:** Why credit belongs in the macro pipeline at all
- **Post 15:** What OAS measures and how to read it
- **Post 16:** The quality spectrum — IG, HY, CCC, and what the gaps between them signal
- **Post 17:** How credit leads equity — and what today's synchronization implies
- **Post 18:** The regime framework — where we are and what would change it

The credit module is now in the pipeline. It runs alongside yield curve, employment, GDP, inflation, volatility, correlation, and sector money flow. Eight modules reading the same macro moment from different angles.

---

## What's Next: Money Flows

The final missing piece. Credit tells you about the price of borrowing. Money flows tell you about where capital is actually moving — which sectors are receiving it, which are losing it, and what that predicts for relative performance.

The next series builds out cross-asset flow analysis. We'll extend the sector money flow tool into a full capital flow monitor: equity sectors, bond markets, commodities, and international flows. The goal is to see rotation before price confirms it.

After that, the pipeline unifies into a daily dashboard — all eight modules in a single morning run. That is where this series has been heading since post one.

---

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

*← [Post 17: Credit vs Equity](#) | [Post 19: Money Flows →](#)*

— *DeltaTheta*
