# Charting the Fed's Constraint — GDP Growth vs. Inflation

*DeltaTheta | Post 9 of the Build Series*

*Written by Claude with oversight.*

The last two posts covered GDP and inflation separately. This one puts them on the same chart — because the relationship between them is where monetary policy lives.

![GDP Growth vs. Inflation — The Fed's Constraint](../.tmp/gdp_vs_inflation.png)

The blue fill is real GDP growth (right axis, quarterly, annualized). Blue above zero is expansion; red below is contraction. The lines are inflation: Core PCE in blue (the Fed's target series) and CPI in red, both year-over-year percent change (left axis, monthly).

---

## Four Regimes in One Chart

**2006–2009: Pre-crisis and collapse.** Inflation was running 2–4% while growth was positive. Then both collapsed simultaneously — GDP dropped sharply into the GFC recession, and inflation followed as demand evaporated. This is the textbook deflationary recession: the Fed had room to cut aggressively because both mandates were pointing the same direction.

**2010–2019: The long expansion.** A decade of GDP growing at 2–3% while inflation consistently undershot 2%. The Fed spent most of this period trying to *raise* inflation, not contain it. The flat lines on the left axis tell that story — Core PCE barely touched 2% before 2018. Growth was steady; the inflation constraint was absent.

**2020–2022: COVID and the supply shock.** The vertical blue spike downward in 2020 is the sharpest quarterly GDP contraction in modern history. The equally sharp recovery followed within two quarters — the fastest V-shape in the dataset. Then, as supply chains broke and fiscal stimulus collided with reopening demand, inflation surged. Both CPI and Core PCE hit levels not seen since the early 1980s. GDP was growing strongly at the same moment inflation was spiking — a combination that removed the Fed's ability to look past it.

**2023–2026: Disinflation and the re-acceleration.** Inflation came down from its 2022 peak as rate hikes took hold. But the chart shows it didn't reach 2%. Core PCE stabilized around 3–3.5% — above target. And by early 2026, both CPI and Core PCE are trending back up while GDP growth has decelerated to the 0.5–1.6% range. That divergence — growth slowing, inflation re-accelerating — is the current regime.

---

## Why This Regime Is Harder

When growth and inflation move together, the Fed's dual mandate resolves cleanly. A weak economy with low inflation: cut. A strong economy with high inflation: hike. The harder case is when they diverge — slowing growth on one side, sticky inflation on the other. The Fed can't address both simultaneously. Every rate decision becomes a tradeoff.

That's the setup in the current data. The bond market (breakeven inflation ~2.4%) is pricing eventual mean-reversion to target. The actual monthly CPI prints (3.95% in April 2026) suggest the path there is not straight. The gap between those two numbers is where the uncertainty lives.

---

## Reproducing the Chart

Two commands. First fetch the data, then render:

```cmd
python tools/fred_fetch.py --series A191RL1Q225SBEA PCEPILFE CPIAUCSL --start 2005-01-01 --out .tmp/fred_gdp_vs_inflation.csv
```

```cmd
python tools/chart_macro.py --csv .tmp/fred_gdp_vs_inflation.csv --left PCEPILFE CPIAUCSL --yoy PCEPILFE CPIAUCSL --right A191RL1Q225SBEA --fill-zero A191RL1Q225SBEA --rename "PCEPILFE:Core PCE (Fed Target)" "CPIAUCSL:CPI" "A191RL1Q225SBEA:GDP Growth Rate" --recessions --title "GDP Growth vs. Inflation" --left-label "Inflation YoY %" --right-label "GDP Growth Rate (QoQ Ann. %)" --out .tmp/gdp_vs_inflation.png
```

The `--yoy` flag converts the CPI and PCE index levels to year-over-year percent change before plotting. The `--fill-zero` flag shades GDP growth bars blue above zero and red below. The `--recessions` flag fetches NBER recession dates from FRED and adds the gray bands automatically.

---

## What's Next

The macro foundation is now in place: rates, positioning, employment, growth, and inflation. The next layer is more immediately actionable — **volatility**. The VIX term structure, realized vs. implied, and what the options market is pricing as tail risk. When volatility diverges from what the macro backdrop suggests, that divergence is often the trade.

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
