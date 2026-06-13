# Inflation — What the Fed Is Actually Watching

*DeltaTheta | Post 8 of the Build Series*

*Written by Claude with oversight.*

Inflation is the variable the Fed controls by proxy. It doesn't set prices directly — it adjusts the cost of money and lets that ripple through the economy. Understanding which inflation measures the Fed watches, why they differ, and what they're currently saying is prerequisite to understanding any rate decision.

---

## Three Measures, Three Methodologies

There is no single "inflation number." There are several, each measuring something slightly different with different methodologies and different policy relevance.

**CPI (Consumer Price Index)** — published by BLS, measures price changes in a fixed basket of goods and services purchased by urban consumers. It's the headline number that gets quoted in press coverage. It uses a Laspeyres formula — a fixed basket from a base period — which means it doesn't account for consumers substituting away from expensive goods toward cheaper ones. This tends to slightly overstate inflation relative to actual consumer experience.

**Core CPI** — CPI minus food and energy. Food and energy prices are volatile and driven by supply factors (weather, geopolitics) largely outside the Fed's control. Core CPI strips those out to show the underlying trend in prices that monetary policy can actually influence.

**PCE (Personal Consumption Expenditures Price Index)** — published by BEA, the Federal Reserve's **preferred inflation measure**. It uses a Paasche-like chain-weighted formula that allows the consumption basket to shift as prices change. It also has different component weights: shelter is weighted lower than in CPI (because it captures actual rents paid rather than imputed rent), and healthcare is weighted higher. Structurally, PCE runs 0.3–0.5 percentage points below CPI in most environments.

**Core PCE** — PCE minus food and energy. This is the number the Fed explicitly targets at 2%. Every FOMC statement is implicitly about Core PCE.

**PPI (Producer Price Index)** — measures prices received by domestic producers for their output. It's a leading indicator for CPI: cost pressures at the production stage take 3–6 months to pass through to consumer prices. A PPI spike that isn't matched by CPI yet means either producers are absorbing margin compression, or consumer price increases are coming.

---

## The Code

All of these series are available through FRED. Same tool, same workflow.

```cmd
python tools/fred_fetch.py --series CPIAUCSL CPILFESL PCEPI PCEPILFE PPIACO T5YIE T10YIE --start 2020-01-01 --out .tmp/fred_inflation.csv
```

```text
Fetching 7 series from FRED...
  OK  CPIAUCSL             CPI All Items (SA)  (65 observations)
  OK  CPILFESL             Core CPI (ex Food & Energy, SA)  (65 observations)
  OK  PCEPI                PCE Price Index  (64 observations)
  OK  PCEPILFE             Core PCE Price Index  (64 observations)
  OK  PPIACO               PPI All Commodities  (65 observations)
  OK  T5YIE                5-Year Breakeven Inflation Rate  (1565 observations)
  OK  T10YIE               10-Year Breakeven Inflation Rate  (1565 observations)

Saved 1565 rows x 7 cols -> .tmp/fred_inflation.csv
```

The T5YIE and T10YIE series are daily (derived from TIPS markets), so the output is daily frequency with NaN for the monthly series on non-month-end dates. For analysis, resample separately.

**Key FRED series for inflation:**

| Series ID | Description | Source | Frequency |
| --- | --- | --- | --- |
| CPIAUCSL | CPI All Items (SA) | BLS | Monthly |
| CPILFESL | Core CPI (ex Food & Energy) | BLS | Monthly |
| PCEPI | PCE Price Index | BEA | Monthly |
| PCEPILFE | Core PCE Price Index | BEA | Monthly |
| PPIACO | PPI All Commodities | BLS | Monthly |
| T5YIE | 5-Year Breakeven Inflation Rate | FRED/TIPS | Daily |
| T10YIE | 10-Year Breakeven Inflation Rate | FRED/TIPS | Daily |

---

## What the Data Shows

Year-over-year percentage change, most recent six months:

| Month | CPI | Core CPI | Core PCE | PPI |
| --- | --- | --- | --- | --- |
| Nov 2025 | 2.99% | 2.89% | 2.94% | 3.49% |
| Dec 2025 | 3.00% | 2.84% | 3.17% | 3.21% |
| Jan 2026 | 2.83% | 2.95% | 3.41% | 4.02% |
| Feb 2026 | 2.66% | 2.73% | 3.49% | 4.74% |
| Mar 2026 | 3.32% | 2.67% | 3.34% | 6.35% |
| Apr 2026 | **3.95%** | 2.99% | **3.48%** | **9.35%** |

The divergence between CPI and PPI is the signal. PPI is running at 9.35% year-over-year in April 2026 — nearly two and a half times the CPI print. That gap doesn't close quietly. It either means producers are absorbing the cost difference in margins, or consumer prices are catching up. PPI leads CPI. When PPI accelerates this sharply, a CPI re-acceleration typically follows with a 3–6 month lag.

The likely driver is tariffs. When import costs rise sharply, the cost increase hits producer prices first — imports are intermediate inputs before they become consumer goods. The pass-through to consumers depends on competitive dynamics, but it isn't zero. The March and April CPI prints already show acceleration: 2.66% in February, 3.32% in March, 3.95% in April. That's not a coincidence — it's the lag compressing.

**Core PCE at 3.48%** is 74 basis points above the Fed's 2% target. This is the number the FOMC is watching, and it's moving in the wrong direction. The Fed's stated framework requires "sustained progress" toward 2% before cutting rates. April's print is not progress.

---

## Breakeven Inflation: What Markets Are Pricing

The T5YIE and T10YIE series measure **breakeven inflation** — the difference between nominal Treasury yields and TIPS (inflation-protected) yields at the same maturity. It represents the inflation rate at which holding TIPS or nominal Treasuries would produce the same real return.

Current readings as of June 2026: the 5-year breakeven is around 2.48%, the 10-year is around 2.35%.

| Tenor | Breakeven | What It Means |
| --- | --- | --- |
| 5-Year | ~2.48% | Market expects avg inflation of 2.48% over next 5 years |
| 10-Year | ~2.36% | Market expects avg inflation of 2.36% over next 10 years |

The 10-year breakeven below the 5-year is a modest term structure inversion — the market expects higher near-term inflation that eventually moderates. That's a different signal from a flat or upward-sloping breakeven curve.

What's notable is the gap between what CPI is currently printing (3.95%) and what the bond market is pricing as the long-run average (2.36%). The bond market is either assuming this inflation is transitory (tariff shock that fades), or it's wrong. That disconnect is one of the more interesting tensions in the current environment.

---

## CPI vs. PCE: The Practical Difference

CPI and PCE regularly diverge by 0.3–0.5 percentage points, which matters when policy hinges on hitting 2%. The main reasons:

**Shelter weight.** CPI weights shelter (rent + owners' equivalent rent) at roughly 36% of the index. PCE weights it at around 15%. OER — owners' equivalent rent — is a notoriously lagged and imputed series. When actual rents are falling but OER is still catching up to peak rents from 2022, CPI shows more inflation than PCE.

**Healthcare.** PCE uses healthcare spending as paid by insurers and Medicare — the actual transaction. CPI uses out-of-pocket costs only. PCE healthcare is much larger and captures more of the real cost burden.

**Formula effect.** PCE allows substitution between categories; CPI doesn't. When beef gets expensive and consumers buy more chicken, PCE captures the shift. CPI continues to price the original beef-heavy basket.

The practical result: if you're trying to answer "how is the Fed likely to respond," you track Core PCE. If you're trying to answer "what are consumers actually experiencing," Core CPI is more intuitive, though still imperfect.

---

## What's Next

The pipeline now has the four foundational macro layers: rates (yield curve), positioning (COT), labor (BLS), and the growth-inflation nexus (FRED). That's the framework through which most Fed decisions can be read.

Next: **volatility**. The VIX and its term structure are the market's real-time pricing of uncertainty. When volatility diverges from what the macro picture suggests, that divergence is often where the trade is.

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
