# GDP and Growth — What the Economy Is Actually Doing

*DeltaTheta | Post 7 of the Build Series*

*Written by Claude with oversight.*

The yield curve tells you where rates are going. Employment tells you how tight the labor market is. GDP tells you whether any of it is actually growing.

Gross Domestic Product is the broadest single measure of economic output — the total market value of goods and services produced in a country over a quarter. It's the number that determines whether you're in an expansion or a recession, and it's the benchmark against which every other macro indicator is calibrated. If yields are rising and growth is accelerating, that's one regime. If yields are rising and growth is contracting, that's something else entirely.

---

## The Accounting Identity

GDP is defined by an identity, not a model:

**GDP = C + I + G + NX**

- **C (Consumption)** — household spending on goods and services. Roughly 70% of US GDP. The single largest component by a wide margin.
- **I (Investment)** — business spending on plant, equipment, software, and residential construction. Volatile. Leads the cycle — investment typically turns down before recessions and up before recoveries.
- **G (Government)** — federal, state, and local government spending on goods and services. Excludes transfer payments (Social Security, Medicare) since those are redistribution, not production.
- **NX (Net Exports)** — exports minus imports. When the US imports more than it exports, NX is negative, which subtracts from GDP directly. This is where things got interesting in early 2025.

Understanding the identity matters because a GDP print is not a single signal — it's a composite. A negative quarter driven by a trade deficit is structurally different from a negative quarter driven by collapsing consumer spending. The number alone doesn't tell you which it is.

---

## The Code

GDP and its components are available through FRED. No separate tool needed — `tools/fred_fetch.py` handles quarterly and monthly series in the same call.

```cmd
python tools/fred_fetch.py --series GDPC1 A191RL1Q225SBEA PCE GPDI GCE NETEXP --start 2020-01-01 --out .tmp/fred_gdp_growth.csv
```

```text
Fetching 6 series from FRED...
  OK  GDPC1                Real GDP (Chained 2017 Dollars)  (21 observations)
  OK  A191RL1Q225SBEA      GDP Growth Rate (QoQ Annualized)  (21 observations)
  OK  PCE                  Personal Consumption Expenditures  (64 observations)
  OK  GPDI                 Gross Private Domestic Investment  (21 observations)
  OK  GCE                  Government Consumption Expenditures  (21 observations)
  OK  NETEXP               Net Exports  (21 observations)

Saved 64 rows x 6 cols -> .tmp/fred_gdp_growth.csv
```

The series have different frequencies — GDPC1 and the components are quarterly, PCE is monthly. FRED handles this gracefully; quarterly series show NaN on non-quarter months. For analysis, filter to quarters.

**Key FRED series for growth:**

| Series ID | Description | Frequency |
| --- | --- | --- |
| GDPC1 | Real GDP, Chained 2017 Dollars | Quarterly |
| GDP | Nominal GDP | Quarterly |
| A191RL1Q225SBEA | Real GDP Growth Rate (QoQ, Annualized) | Quarterly |
| PCE | Personal Consumption Expenditures | Monthly |
| GPDI | Gross Private Domestic Investment | Quarterly |
| GCE | Government Consumption Expenditures | Quarterly |
| NETEXP | Net Exports of Goods and Services | Quarterly |
| INDPRO | Industrial Production Index | Monthly |

---

## What the Data Shows

Running the last eight quarters:

| Quarter | Real GDP ($B) | Growth Rate | PCE | Investment | Gov't | Net Exports |
| --- | --- | --- | --- | --- | --- | --- |
| Q2 2024 | 23,287 | 3.6% | 19,666 | 5,290 | 4,995 | −894 |
| Q3 2024 | 23,479 | 3.3% | 19,950 | 5,330 | 5,087 | −938 |
| Q4 2024 | 23,587 | 1.9% | 20,226 | 5,262 | 5,151 | −939 |
| Q1 2025 | 23,548 | **−0.6%** | 20,462 | 5,556 | 5,196 | **−1,265** |
| Q2 2025 | 23,771 | 3.8% | 20,746 | 5,359 | 5,237 | −900 |
| Q3 2025 | 24,027 | **4.4%** | 21,007 | 5,419 | 5,324 | −757 |
| Q4 2025 | 24,056 | 0.5% | 21,288 | 5,501 | 5,344 | −785 |
| Q1 2026 | 24,153 | 1.6% | 21,509 | 5,620 | 5,416 | −895 |

Three things stand out.

**Q1 2025 was a fake contraction.** The GDP print came in at −0.6% — technically negative, which sent recession alarms through financial media. But look at the components. Consumer spending rose $236B from Q4 2024. Investment rose $294B. Government spending rose $45B. Every domestic demand component was growing. What collapsed was net exports: from −$939B to −$1,265B in a single quarter, a $326B swing.

That's companies front-running tariffs. Businesses that expected import costs to rise sharply in Q2 and beyond pulled orders forward — importing heavily in Q1 to build inventory before tariffs hit. Mechanically, imports subtract from GDP. The domestic economy was fine. The GDP number was distorted by a rational response to policy.

**The bounce confirmed it.** Q2 2025 came in at 3.8%, Q3 at 4.4%. When the import surge normalized, the mechanical drag reversed and underlying growth reasserted. That V-shape is not what genuine recessions look like.

**Investment is the live signal now.** GPDI hit $5,620B in Q1 2026, the highest in the dataset. Business investment leading growth is a different signal than consumer spending leading growth — the former reflects corporate confidence in future demand, the latter can be driven by balance sheet drawdown. Worth watching whether that investment pace holds.

---

## Real vs. Nominal, and Why It Matters

GDPC1 is **real** GDP — adjusted for inflation using 2017 as the base year. When the economy grows 3% nominally but inflation is running 3%, real GDP growth is approximately zero. The distinction matters most when inflation is elevated.

In 2022, nominal GDP grew roughly 9%. Real GDP grew less than 2%. The difference was inflation. An investor looking at nominal GDP as a growth signal in that environment was reading noise.

For macro analysis, always use GDPC1 (real) for level comparisons and A191RL1Q225SBEA for the quarterly growth rate. Use nominal GDP only when you specifically need it — debt-to-GDP ratios, for instance, use nominal because debt is nominal.

---

## What's Next

GDP tells you what already happened — it's released with a 30-day lag and revised twice after that. It's a lagged indicator. The forward-looking version of the growth question is what the leading indicators — yield curve, credit spreads, PMI surveys — are pricing. We'll build that dashboard later.

The next piece is the other half of the macro picture: **inflation**. Growth is running at 1.6% annualized. Prices are rising at 3.5–4%. That divergence — slowing growth, sticky inflation — is the regime question that sets the policy context for everything else in the pipeline.

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
