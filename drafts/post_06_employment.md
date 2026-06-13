# Employment Data — The Other Half of the Fed's Job

*DeltaTheta | Post 6 of the Build Series*

*Written by Claude with oversight.*

The yield curve tells you what the bond market expects the Fed to do. Employment data tells you why.

The Federal Reserve has a dual mandate: price stability and maximum employment. That's not a figure of speech — it's written into the Federal Reserve Act. Every rate decision is a tradeoff between those two objectives. When you understand where employment stands, you understand the constraint the Fed is operating under. And when you know the constraint, the yield curve interpretation sharpens considerably.

This post adds the employment layer to the pipeline.

---

## Two Surveys, One Report

The Employment Situation — what markets call the "jobs report" — is released on the first Friday of each month by the Bureau of Labor Statistics. It combines two independent surveys that measure the labor market from different angles.

**The Establishment Survey (payrolls)** asks businesses how many people they employed. This is the source of the headline number: Nonfarm Payrolls, or NFP. It covers about 119,000 businesses and government agencies. It's broad, it's consistent, and it's heavily revised — the first release often differs from the third and final revision by 50,000 to 100,000+ jobs. The number you see on Friday morning is an estimate.

**The Household Survey (unemployment)** asks individuals whether they're employed, unemployed, or out of the labor force. This is where the unemployment rate comes from. It's a smaller sample (~60,000 households), which makes it noisier month to month, but it captures things the Establishment Survey misses — self-employment, agricultural workers, and people who work for multiple employers.

They often tell slightly different stories in any given month. When they diverge meaningfully over several months, that divergence is itself a signal worth examining.

---

## The Series That Actually Matter

The headline unemployment rate is U-3: unemployed workers actively seeking work as a percentage of the labor force. It's what gets quoted on the news. It's also the most optimistic measure of labor market slack.

**U-6** is broader: U-3 plus workers marginally attached to the labor force (want work but stopped looking) plus people working part-time for economic reasons (want full-time, can't find it). It's consistently about 1.8–2.0x the U-3 number. When that ratio widens — when U-6 grows faster than U-3 — it indicates deteriorating quality of employment, not just headline weakness.

**Average Hourly Earnings** is the wage signal the Fed watches closely. Wage growth feeds into services inflation with a lag. When payrolls are still growing but wage growth is decelerating, the labor market is softening without yet breaking. When wage growth reaccelerates while unemployment is rising, you have a stagflationary dynamic.

**Labor Force Participation Rate** measures what fraction of the working-age population is either employed or actively looking for work. The Fed can't use monetary policy to pull workers off the sidelines — structural participation changes (aging demographics, disability, caregiving) are beyond its tools. This matters because a falling unemployment rate driven by discouraged workers leaving the labor force looks like progress but isn't.

---

## The Code: bls_fetch.py

The tool is at `tools/bls_fetch.py`. It hits the BLS public API v2 directly — no API key required, no authentication, completely free. With a registered key (free at bls.gov) you get extended history and larger batch requests; without one, the tool auto-chunks requests into 10-year windows and handles it transparently.

```bash
# Employment dashboard — unemployment, payrolls, earnings, participation
python tools/bls_fetch.py

# Specify a date range
python tools/bls_fetch.py --start 2015 --end 2025

# NFP sector breakdown — who is adding or losing jobs
python tools/bls_fetch.py --preset sectors --out .tmp/bls_sectors.csv

# Wage detail
python tools/bls_fetch.py --preset wages --out .tmp/bls_wages.csv

# Any specific BLS series by ID
python tools/bls_fetch.py --series LNS14000000 LNS13327709 CES0000000001

# See all preset series IDs
python tools/bls_fetch.py --list-series
```

Running the dashboard preset against 2022–2025:

```
Fetching 6 BLS series (2022–2025):
  LNS14000000  Unemployment Rate (U-3, SA)
  LNS13327709  U-6 Unemployment (Broad, SA)
  LNS11300000  Labor Force Participation Rate (SA)
  CES0000000001  Total Nonfarm Payrolls (thousands, SA)
  CES0500000003  Avg Hourly Earnings, All Private (SA)
  CES0500000002  Avg Weekly Hours, All Private (SA)

  Fetching 6 series: 2022–2025 ... 48 rows

Saved 48 rows x 6 series -> .tmp/bls_employment_2022_2025.csv

            U-3    U-6    LFPR   NFP (000s)   Hrly Earn   Wkly Hrs
2025-07-01  4.3    7.9    62.2   158,542      $36.47      34.2
2025-08-01  4.3    8.1    62.3   158,472      $36.62      34.2
2025-09-01  4.4    8.1    62.5   158,548      $36.70      34.2
2025-10-01  NaN    NaN    NaN    158,408      $36.85      34.2
2025-11-01  4.5    8.7    62.5   158,449      $37.00      34.3
2025-12-01  4.4    8.4    62.4   158,432      $37.02      34.2
```

A few things visible in that tail.

**U-3 at 4.4%** is above the 2023 cycle low of ~3.4% but not at levels that historically signal recession onset. The Fed's longer-run neutral estimate for unemployment is around 4.2%, so we're sitting slightly above that — modest labor market slack, not deterioration.

**U-6 at 8.4%** puts the ratio at about 1.9x U-3, which is near the normal range. The November spike to 8.7% U-6 while U-3 held at 4.5% is worth watching — a widening ratio can signal quality-of-employment erosion before the headline number moves.

**NFP around 158 million** — that's the total employed, and it's been remarkably stable at this level. Monthly changes are measured in the tens of thousands, not millions. Context matters: 150,000 new jobs in a month is historically consistent with trend growth; 300,000+ was the post-pandemic surge; below 75,000 starts to raise recession flags.

**Hourly earnings at $37.02** — wage growth is still present but flattening. The pace of increase from $36.47 in July to $37.02 in December is about 1.5% over six months (roughly 3% annualized). That's at the low end of what the Fed considers consistent with 2% inflation given productivity assumptions.

---

## The Sector Breakdown

The NFP number hides substantial variation underneath. Running `--preset sectors`:

```
python tools/bls_fetch.py --preset sectors --start 2023 --end 2025 --out .tmp/bls_sectors.csv
```

| Date     | Total (000s) | Mfg    | Ed/Health | Leisure | Fed Gov |
| -------- | ------------ | ------ | --------- | ------- | ------- |
| Jun 2025 | 158,478      | 12,636 | 27,325    | 16,837  | 2,944   |
| Jul 2025 | 158,542      | 12,625 | 27,412    | 16,848  | 2,935   |
| Aug 2025 | 158,472      | 12,615 | 27,435    | 16,870  | 2,916   |
| Sep 2025 | 158,548      | 12,612 | 27,489    | 16,907  | 2,914   |
| Oct 2025 | 158,408      | 12,603 | 27,533    | 16,948  | 2,748   |
| Nov 2025 | 158,449      | 12,593 | 27,589    | 16,936  | 2,733   |
| Dec 2025 | 158,432      | 12,580 | 27,627    | 16,961  | 2,722   |

Two things stand out immediately.

**Federal government employment dropped sharply**: from 2,944K in June to 2,722K in December — a decline of 222,000 jobs over six months. That's the DOGE-era federal workforce reduction showing up in the data. It's significant enough to have suppressed NFP from what it otherwise would have been, and it's a structural headwind the private sector has to absorb.

**Education & Health keeps grinding higher**: 27,325K in June to 27,627K in December, +302K over the same period. This sector has been the single largest consistent contributor to NFP for several years — it largely offsets the federal decline in the aggregate number. But these are structurally different jobs with different wage dynamics, demand drivers, and inflation implications.

**Manufacturing is slowly contracting**: 12,636K in June to 12,580K in December, −56K. Gradual, but directionally consistent with what the ISM surveys have been saying about factory activity.

---

## A Note on Revisions

The first NFP print is preliminary. BLS revises it twice in subsequent months and again in annual benchmark revisions. The difference between initial and final can be material — during the 2022–2023 period, several monthly prints were revised by 50,000–100,000+ jobs.

This has a practical implication: if you build signals using employment data and backtest them, the data your model "sees" at decision time is different from what the historical record shows after revisions. The BLS API returns the current vintage — the fully revised numbers — not what was available in real time. Document this caveat in any signal research.

---

## What's Next

The pipeline now has: yield curve (FRED), positioning (CFTC COT), and labor market (BLS). The analytical layer — charting these together, normalizing against history — is where the interpretation lives.

Before building that layer, the next post goes somewhere more immediately actionable: **volatility data**. VIX, term structure, realized vs. implied — the volatility surface tells you what the options market is pricing as risk, which is a different signal than what the rates or positioning markets are saying. When they diverge, that divergence is tradeable.

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
