# OAS 101: What Credit Spreads Actually Measure

*DeltaTheta | Post 15 of the Build Series*

*Written by Claude with oversight.*

A spread is a difference. A credit spread is the difference between the yield on a corporate bond and the yield on a comparable Treasury. If a 10-year corporate bond yields 6% and the 10-year Treasury yields 4.3%, the spread is 170 basis points. That 170bps is the market's price for taking on the risk that the corporate borrower might not pay you back.

Simple in concept. Harder in practice, because most corporate bonds are callable — the issuer can redeem them early if rates fall in their favor. That embedded option has value, and it distorts the raw yield spread. **Option-Adjusted Spread (OAS)** strips out the value of that embedded option, leaving a clean measure of pure credit risk premium. OAS is what you get when you ask: ignoring the issuer's right to call this bond, how much extra yield am I actually being paid to take on credit risk?

That's the number this pipeline now tracks.

---

## The FRED Series

The ICE BofA indices are the standard institutional reference for aggregate OAS. They aggregate hundreds of bonds in each tier, market-value weight them, and compute a single daily spread reading. FRED carries the series directly.

| FRED ID | What It Tracks |
|---|---|
| BAMLH0A0HYM2 | US High Yield OAS — bonds rated BB and below |
| BAMLC0A0CM | US Investment Grade OAS — bonds rated BBB and above |
| BAMLH0A3HYC | US CCC-Rated OAS — the most distressed tier |

High yield (HY) is the primary signal. It's the tier most sensitive to credit stress — the companies in the HY index have less financial cushion, so the spread moves first and moves more when conditions shift.

---

## The Tool

`tools/credit_spreads.py` pulls these series from FRED and produces a current-reading summary with 52-week context and percentile rank.

```
python tools/credit_spreads.py
python tools/credit_spreads.py --series HY IG CCC
python tools/credit_spreads.py --chart
python tools/credit_spreads.py --start 2010-01-01 --chart
```

The percentile rank answers a question that a raw spread number doesn't: is this level high or low relative to history? A spread of 3% means very different things depending on whether that's the tightest level in years or the widest.

---

## Today's Reading

```
python tools/credit_spreads.py --series HY IG --chart

Fetching credit spread data from FRED...
  OK  BAMLH0A0HYM2           US High Yield OAS  (795 obs)
  OK  BAMLC0A0CM             US Investment Grade OAS  (795 obs)

Credit Spread Snapshot  —  2026-06-21
====================================================================
  Series                      Current   52W Low  52W High   Pctile   WoW Chg
--------------------------------------------------------------------
  US High Yield OAS             2.63%     2.63%     3.46%     1.4%     -0.17
  US Investment Grade OAS       0.74%     0.73%     0.94%     1.0%     -0.01
====================================================================
  Source: ICE BofA via FRED  |  OAS = Option-Adjusted Spread over Treasuries
```

![Credit Spread History — HY and IG OAS](../.tmp/credit_spreads_20260621.png)

---

## What This Is Saying

**HY OAS at 2.63% — 1.4th percentile.** Credit has been this tight or tighter on only 1.4% of trading days in the data history. That is not a normal reading. The market is pricing near-zero probability of credit stress — almost no default risk premium above what the risk-free rate already compensates.

**IG OAS at 0.74% — 1.0th percentile.** Investment grade spreads are even tighter in historical context. At this level, IG bondholders are being paid almost nothing for the risk of holding corporate rather than government paper.

**Week-over-week: HY tightened another 17bps.** The direction of the last five sessions is toward even more compression, not a reversal.

There are two reads on this:

**The optimistic read:** Credit markets are functioning perfectly. Capital is abundant, refinancing conditions are favorable, and default rates are low. The spread level is telling you the economy is fine.

**The skeptical read:** Spreads this tight leave almost no cushion. They're pricing perfection in an environment that is demonstrably not perfect — sovereign debt at peacetime records, a Fed transition underway, and fiscal dynamics that don't resolve cleanly. When something eventually pressures credit, the move from here could be sharp and fast, precisely because there's so little risk premium to absorb it.

Which read you take depends on your time horizon and risk framework. The pipeline doesn't take a position — it reads. What it's reading right now is extraordinary tightness.

---

## Next: The Spread Spectrum

The next post maps the full credit quality spectrum — investment grade, high yield, and distressed. Each tier prices a different layer of risk and moves on a different timeline when stress arrives. Understanding the spread hierarchy is what lets you use credit as a leading indicator rather than a coincident one.

---

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
