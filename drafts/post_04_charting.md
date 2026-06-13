# Charting the Yield Curve — Building the Visualization Layer

*DeltaTheta | Post 4 of the Build Series*

*Written by Claude with oversight.*

Post 3 ended with a CSV: 6,651 rows of yield curve data, date-indexed, ready to use. This post turns that into something you can actually read.

Visualization isn't decoration. A chart is where patterns in a data series become visible as structure — inversions, the timing relative to recessions, how the current level compares to prior cycles. You can't see that in a CSV. The charting layer is part of the analytical infrastructure, not a finishing step.

---

## What the Chart Needs to Show

The yield curve chart has a specific layout problem: we want to plot two different things on the same time axis.

On the left, absolute yields — the 2-year and 10-year Treasury rates in percent. These move together most of the time, driven by the level of interest rates in the economy. In 2022–2023, both were rising. In 2024–2025, both were falling.

On the right, the spread — the difference between them in percentage points. This is a much smaller number (fractions of a point, sometimes negative) that would be visually crushed if plotted on the same axis as the yields themselves. We want to see the spread move independently, shaded to distinguish positive from negative.

On top of everything, recession bands — gray shading marking the NBER-designated recession periods, so the predictive relationship between inversion and contraction is visible directly on the chart.

That's a dual-axis chart with fill logic and overlaid shading. Here's the command that produces it:

```cmd
python tools/chart_macro.py --csv .tmp/fred_DGS2_DGS10_T10Y2Y_20260612.csv --left DGS2 DGS10 --right T10Y2Y --fill-zero T10Y2Y --recessions --title "US Yield Curve: 2Y vs 10Y and Spread (2000-2026)" --out .tmp/yield_curve_2000_2026.png
```

![US Yield Curve 2000–2026](../.tmp/yield_curve_2000_2026.png)

---

## The Code: chart_macro.py

The tool is at `tools/chart_macro.py`. The core is a `plot()` function that accepts a DataFrame and a set of column assignments, then builds the chart in layers.

**Layer 1 — Recession shading.** Drawn first, behind everything else. The tool fetches the USREC series from FRED (1 = recession, 0 = expansion), finds contiguous recession periods, and shades them gray. This uses the same `Fred` client as `fred_fetch.py` — same API key, same SSL patch.

```python
for rec_start, rec_end in recession_bands:
    ax1.axvspan(rec_start, rec_end, color=RECESSION_COLOR, alpha=0.6, zorder=0)
```

**Layer 2 — Left axis series.** The absolute yields plotted as solid lines. Each series gets a color from a fixed palette in sequence: blue, red, green, orange, purple, gray. Consistent across every chart we produce.

**Layer 3 — Right axis (spread with fill).** The spread series gets special treatment when `--fill-zero` is set. We plot the line in gray, then use `fill_between` twice — once for values above zero (light blue, normal curve) and once for values below zero (light red, inverted curve).

```python
ax2.fill_between(
    series.index, series.values, 0,
    where=(series.values >= 0),
    color=SPREAD_POS_COLOR, alpha=0.7,   # "#BFDBFE" — light blue
)
ax2.fill_between(
    series.index, series.values, 0,
    where=(series.values < 0),
    color=SPREAD_NEG_COLOR, alpha=0.7,   # "#FECACA" — light red
)
```

The zero line is drawn as a dashed gray reference. When the red fill appears, the curve has inverted.

**Layer 4 — Annotations.** The latest value for each left-axis series is labeled at the right edge of the chart. Small, gray, precise — so the chart is self-contained without requiring a data table alongside it.

**Output.** PNG at 150 DPI, saved to the specified path. `bbox_inches="tight"` ensures the title and axis labels aren't clipped.

---

## What the Chart Tells You

With recession shading in place, the pattern is hard to miss. The curve inverted before the 2001 recession. It inverted before the 2008 recession. It inverted briefly before the 2020 recession (though COVID compressed that cycle). And it inverted sharply in 2022–2024 — the deepest inversion in the modern record — before re-steepening without a conventional recession following.

That last case is why post 3 included the caveat: inversion is a necessary-but-not-sufficient condition. The chart makes the track record visible, and it makes the exception visible too. Both are useful.

The current shape — a modest positive spread, re-steepening from deep inversion — is the kind of thing that looks one way on a data table and a very different way on a 26-year chart with cycle context. The chart is how you hold the current observation against history.

---

## Tool Design Notes

A few decisions worth documenting for when this tool gets extended.

**The dual-axis legend is manually merged.** Matplotlib doesn't combine legends from two axes automatically. We pull handles and labels from both axes, filter out internal labels (those starting with `_`), and pass them together to a single legend call. Messy but necessary.

**The `seaborn-v0_8-whitegrid` style.** Seaborn's style naming changed across versions; the `v0_8` prefix is the stable way to reference it in newer matplotlib. If the style call fails on a fresh environment, this is likely the cause.

**The tool is intentionally narrow.** `chart_macro.py` produces time-series line charts from FRED CSVs. It doesn't handle bar charts, scatter plots, or heatmaps. When we build those, they'll be separate tools with their own workflows — scoped, testable, callable independently.

---

## What the Directory Looks Like Now

```
DnT/
├── CLAUDE.md
├── .env
├── tools/
│   ├── fred_fetch.py          ← pull any FRED series to CSV
│   ├── chart_macro.py         ← generate publication-quality time-series charts
│   ├── make_header.py         ← generate Substack header images
│   └── substack_post.py       ← push drafts to Substack
├── workflows/
│   ├── fred_data.md
│   └── substack_post.md
└── .tmp/
    ├── fred_DGS2_DGS10_T10Y2Y_20260612.csv
    └── yield_curve_2000_2026.png
```

Four tools. Two workflows. Everything that's been built in front of you. The Foundation series is nearly complete — data in, charts out, posts published.

---

Next post: **COT Reports — Reading Futures Positioning**. We move into Series 2 and start pulling CFTC Commitments of Traders data. What the positioning data measures, why Commercial vs. Non-Commercial divergence matters, and the script to fetch and parse the weekly COT release.

If you want to follow the build, subscribe. If this has been useful and you'd like to help keep it going — coffee and API tokens are always appreciated.

[☕ Buy me a coffee/tokens](https://www.buymeacoffee.com/DeltanTheta)

— *DeltaTheta*
