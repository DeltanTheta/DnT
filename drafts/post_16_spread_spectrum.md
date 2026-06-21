# The Spread Spectrum: IG, HY, and Distressed

*DeltaTheta | Post 16 of the Build Series*

*Written by Claude with oversight.*

The number from last week — HY OAS at 2.63% — is an aggregate. One number for hundreds of bonds across dozens of industries. Underneath it are three quality tiers, each pricing a different kind of risk, each moving on a different clock. The tier you look at determines what the signal means. The gap between tiers is a signal in its own right.

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

Fetching credit spread data from FRED...
  OK  BAMLH0A0HYM2           US High Yield OAS  (795 obs)
  OK  BAMLC0A0CM             US Investment Grade OAS  (795 obs)
  OK  BAMLH0A3HYC            US CCC-Rated OAS  (795 obs)

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

Fetching recession data...
  Chart -> E:\DnT\.tmp\credit_spreads_20260621.png
  Stack chart -> E:\DnT\.tmp\credit_spreads_stack_20260621.png
```

![Credit Spread History — HY, IG, CCC](../.tmp/credit_spreads_20260621.png)

![Credit Spread Stack — Tier Hierarchy](../.tmp/credit_spreads_stack_20260621.png)

---

## What This Is Saying

The tier breakdown reveals something that the HY headline number alone obscures: this is not a uniform picture.

**IG and HY are at historical extremes. CCC is not.** HY OAS at 2.63% sits at the 1.4th percentile — tighter than 98.6% of all days in the data history. IG OAS at 0.74% is at the 1.0th percentile. Both are near multi-year lows. CCC at 9.39% is at the 75th percentile — elevated relative to the past year, where it hit a low of 7.83%. The distressed end of the market is not pricing in the same serenity as the rest of the credit stack.

**Quality premium compressed but not obliterated.** The HY–IG differential sits at 1.89%, 5.5th percentile — historically tight, meaning the market is charging relatively little extra to move down the quality ladder from investment grade to high yield. But unlike the headline tiers, this is not at an all-time extreme. The compression reflects strong demand for yield across the quality spectrum, but the distressed tier's divergence suggests the market is still making at least some distinctions at the bottom.

**Direction this week: tighter across the board, led by HY.** HY tightened 17bps week-over-week. CCC tightened 18bps. IG moved just 1bp. The move is broad-based rather than concentrated in one tier, which typically signals risk appetite rather than a technical repositioning in a single segment.

Two reads:

**The constructive read:** The bifurcation between IG/HY and CCC is actually healthy price discovery. The investment grade and leveraged finance markets are functioning in an environment of genuine fundamental strength — low default rates, strong refinancing conditions, and corporate balance sheets rebuilt over the last cycle. CCC elevated at the 75th percentile reflects appropriate discrimination: the weakest issuers carry real restructuring risk and the market is pricing it accordingly. This is what rational credit pricing looks like, not distortion.

**The skeptical read:** IG at the 1.0th percentile and HY at the 1.4th percentile are pricing perfection in the strongest-rated segments while CCC at the 75th percentile quietly signals that the weakest borrowers are already under stress. That divergence has a historical precedent: spread compression at the top accompanied by distress at the bottom often precedes a broader repricing. The quality premium at 1.89% — 5.5th percentile — leaves almost no cushion between what the market charges for investment grade and what it charges for junk. When the tide turns, the first move is typically a flight out of HY toward IG, which blows out the quality premium sharply from these levels. Starting from the 5.5th percentile, there is a lot of room for that gap to widen.

No position taken. The pipeline reads; the reader decides.

---

## Next: Credit as a Leading Indicator

The next post turns this into a cross-asset signal. We'll look at the historical relationship between credit spreads and equity — whether spread moves lead or lag equity turns, what the historical case studies show, and what the current configuration implies for equity direction over the next several months.

---

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

*← [Post 15: OAS 101](#) | [Post 17: Credit vs Equity →](#)*

— *DeltaTheta*
