import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from pathlib import Path

def perform_liquiditeit_analysis():
    # ── Data inladen ─────────────────────────────────────────────
    df = pd.read_csv("data/snp500_macro_dataset.csv", parse_dates=["Date"], index_col="Date")
    df = df[["Liquidity_30d_RoC", "SP500_Future_30d_Return"]].dropna()

    x = df["Liquidity_30d_RoC"]
    y = df["SP500_Future_30d_Return"]

    # ── Statistieken ──────────────────────────────────────────────
    slope, intercept, r, p, _ = stats.linregress(x, y)
    r2 = r ** 2

    # ── Scatterplot ───────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))

    # Kleurcodering gebaseerd op kwadranten
    colors = []
    for i in range(len(df)):
        if x.iloc[i] > 0 and y.iloc[i] > 0:
            colors.append("#1D9E75")  # Groen: beide positief
        elif x.iloc[i] > 0 and y.iloc[i] < 0:
            colors.append("#E24B4A")  # Rood: liquiditeit +, markt -
        elif x.iloc[i] < 0 and y.iloc[i] > 0:
            colors.append("#EF9F27")  # Oranje: liquiditeit -, markt +
        else:
            colors.append("#888780")  # Grijs: beide negatief

    ax.scatter(x, y, c=colors, alpha=0.7, edgecolors="black", linewidth=0.5)

    # Regressielijn
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, color="black", linewidth=2, label=f"Regressielijn (R={r:.3f})")

    # Assen door oorsprong
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

    return True