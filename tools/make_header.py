"""
Generate a Substack header image for DeltaTheta.
Output: 1200x630px PNG — standard social/OG card dimensions.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT = Path(__file__).parent.parent / ".tmp" / "header_post01.png"

W, H = 11, 2.2   # inches at 100dpi = 1100x220px

fig, ax = plt.subplots(figsize=(W, H))
fig.patch.set_facecolor("#0A0A0F")
ax.set_facecolor("#0A0A0F")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")

# ── Background grid lines (subtle, like a trading terminal) ──────────────────
for x in np.linspace(0.05, 0.95, 12):
    ax.axvline(x, color="#1A1A2E", linewidth=0.5, zorder=1)
for y in np.linspace(0.05, 0.95, 7):
    ax.axhline(y, color="#1A1A2E", linewidth=0.5, zorder=1)

# ── Fake yield curve sparkline ────────────────────────────────────────────────
np.random.seed(42)
t = np.linspace(0, 1, 300)
# Rough shape: rises, inverts, re-steepens — evocative not literal
curve = (
    0.18
    + 0.08 * np.sin(t * np.pi * 1.2)
    - 0.12 * np.exp(-((t - 0.55) ** 2) / 0.02)
    + 0.04 * t
    + 0.008 * np.random.randn(300).cumsum() / 300
)
# Normalize to sit in lower portion of chart
curve = (curve - curve.min()) / (curve.max() - curve.min())
curve = curve * 0.55 + 0.18
x_start = 0.52
t_plot = x_start + t * (1 - x_start)

# Fill under curve
ax.fill_between(t_plot, curve, 0.18, alpha=0.15, color="#2563EB", zorder=2)
ax.plot(t_plot, curve, color="#2563EB", linewidth=1.5, alpha=0.55, zorder=3)

# Highlight the inversion dip in red
inv_mask = curve < 0.38
if inv_mask.any():
    ax.fill_between(t_plot, curve, 0.38,
                    where=inv_mask,
                    color="#DC2626", alpha=0.35, zorder=4)

# ── Accent line across top ────────────────────────────────────────────────────
ax.axhline(0.93, xmin=0.02, xmax=0.98, color="#2563EB", linewidth=1.2, zorder=5)

# ── Greek letters — large, faint, behind text ─────────────────────────────────
ax.text(0.82, 0.52, "ΔΘ", fontsize=72, color="#2563EB", alpha=0.07,
        ha="center", va="center", fontweight="bold", zorder=2,
        fontfamily="serif")

# ── Main title (left-aligned for wide banner) ─────────────────────────────────
ax.text(0.04, 0.62, "DeltaTheta", fontsize=34, color="#F8FAFC",
        ha="left", va="center", fontweight="bold", zorder=6,
        fontfamily="sans-serif")

# ── Tagline ───────────────────────────────────────────────────────────────────
ax.text(0.04, 0.35, "Building a Hedge Fund Research Desk for One",
        fontsize=11, color="#94A3B8",
        ha="left", va="center", zorder=6,
        fontfamily="sans-serif", style="italic")

# ── Series label ─────────────────────────────────────────────────────────────
ax.text(0.96, 0.62, "POST 1  ·  THE MANIFESTO",
        fontsize=8, color="#2563EB",
        ha="right", va="center", zorder=6,
        fontfamily="monospace", fontweight="bold", alpha=0.9)

# ── Bottom rule + URL ────────────────────────────────────────────────────────
ax.axhline(0.10, xmin=0.02, xmax=0.98, color="#1E293B", linewidth=0.8, zorder=5)
ax.text(0.96, 0.04, "deltantheta.substack.com",
        fontsize=7, color="#475569",
        ha="right", va="center", zorder=6, fontfamily="monospace")
ax.text(0.04, 0.04, "Macro research infrastructure for independent traders",
        fontsize=7, color="#475569",
        ha="left", va="center", zorder=6, fontfamily="monospace")


plt.tight_layout(pad=0)
fig.savefig(OUT, dpi=100, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"Header saved -> {OUT}")
