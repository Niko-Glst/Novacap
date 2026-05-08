import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from pathlib import Path

# ── Data inladen ─────────────────────────────────────────────
df = pd.read_csv("snp500_macro_dataset.csv", parse_dates=["Date"], index_col="Date")
df = df[["Liquidity_30d_RoC", "SP500_Future_30d_Return"]].dropna()

x = df["Liquidity_30d_RoC"]
y = df["SP500_Future_30d_Return"]

# ── Statistieken ──────────────────────────────────────────────
slope, intercept, r, p, _ = stats.linregress(x, y)
r2 = r ** 2

# ── Plot ──────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))

# Kleur per kwadrant: positief signal + positief rendement = groen etc.
colors = np.where(
    (x > 0) & (y > 0), "#1D9E75",   # liquiditeit omhoog, markt omhoog
    np.where(
        (x > 0) & (y < 0), "#E24B4A",   # liquiditeit omhoog, markt omlaag
        np.where(
            (x < 0) & (y > 0), "#EF9F27",   # liquiditeit omlaag, markt omhoog
            "#888780"                          # liquiditeit omlaag, markt omlaag
        )
    )
)

ax.scatter(x, y, c=colors, alpha=0.5, s=20, linewidths=0)

# Regressielijn
x_line = np.linspace(x.min(), x.max(), 200)
ax.plot(x_line, slope * x_line + intercept, color="#378ADD", linewidth=2, label="Regressielijn")

# Nulassen
ax.axhline(0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)
ax.axvline(0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)

# Kwadrant labels
ax.text(x.max() * 0.95, y.max() * 0.90, "Liquiditeit + / Markt +", fontsize=9, color="#1D9E75", ha="right")
ax.text(x.max() * 0.95, y.min() * 0.90, "Liquiditeit + / Markt -", fontsize=9, color="#E24B4A", ha="right")
ax.text(x.min() * 0.95, y.max() * 0.90, "Liquiditeit - / Markt +", fontsize=9, color="#EF9F27", ha="left")
ax.text(x.min() * 0.95, y.min() * 0.90, "Liquiditeit - / Markt -", fontsize=9, color="#888780", ha="left")

# Stats tekst
stats_tekst = (
    f"R  = {r:.3f}\n"
    f"R² = {r2:.3f}\n"
    f"p  = {p:.4f}\n"
    f"n  = {len(df)}"
)
ax.text(0.02, 0.97, stats_tekst, transform=ax.transAxes,
        fontsize=10, va="top", fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="lightgray"))

ax.set_xlabel("Liquiditeitsgroei 30d (RoC)", fontsize=11)
ax.set_ylabel("S&P 500 rendement volgende 30d", fontsize=11)
ax.set_title("Voorspellende kracht stablecoin liquiditeit op S&P 500 rendement", fontsize=13)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.legend()
ax.grid(True, alpha=0.15)

plt.tight_layout()
plt.savefig(Path("data") / "liquiditeit_vs_rendement.png", dpi=150)
plt.show()

# ── Samenvatting in terminal ──────────────────────────────────
print(f"\nCorrelatie analyse: Liquiditeit RoC → S&P 500 (30d vooruit)")
print(f"{'─'*45}")
print(f"Pearson R        : {r:.3f}")
print(f"R²               : {r2:.3f}")
print(f"p-waarde         : {p:.4f} {'(significant)' if p < 0.05 else '(niet significant)'}")
print(f"Datapunten       : {len(df)}")
print(f"{'─'*45}")

trefkans = ((x > 0) == (y > 0)).mean()
print(f"Richtingskans    : {trefkans:.1%}  (hoe vaak wijst signal de goede kant op)")