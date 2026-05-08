import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# ── Data inladen ─────────────────────────────────────────────
DATA_DIR = Path("data")

vix = pd.read_csv(DATA_DIR / "vix_historical.csv", parse_dates=["date"])
vix.columns = ["date", "VIX"]

sp = pd.read_csv(DATA_DIR / "snp500_price_data.csv", parse_dates=["Date"])
sp = sp[["Date", "Close"]].rename(columns={"Date": "date", "Close": "SP500"})

# ── Samenvoegen op datum ──────────────────────────────────────
df = pd.merge(vix, sp, on="date", how="inner").sort_values("date")

if df.empty:
    print("Geen overlappende datums — beide bestanden hebben een andere periode")
    print(f"VIX periode : {vix['date'].min().date()} - {vix['date'].max().date()}")
    print(f"SP500 periode: {sp['date'].min().date()} - {sp['date'].max().date()}")
    exit()

# ── Transformaties berekenen ──────────────────────────────────
window = 20  # ~1 maand handelsdagen

# 1. S&P 500 returns en rolling volatility
df['SP500_Return'] = df['SP500'].pct_change()
df['SP500_RollingVol'] = df['SP500_Return'].rolling(window=window).std() * np.sqrt(252) * 100

# 2. Rolling Z-score van VIX
df['VIX_Mean'] = df['VIX'].rolling(window=window).mean()
df['VIX_Std'] = df['VIX'].rolling(window=window).std()
df['VIX_ZScore'] = (df['VIX'] - df['VIX_Mean']) / df['VIX_Std']

# 3. Correlatie berekenen (globaal en rolling)
corr_global = df["VIX"].corr(df["SP500"])
df['VIX_SP500_Corr'] = df['VIX'].rolling(window=window).corr(df['SP500'])

# ── Plot - Multi-panel analyse ────────────────────────────────
fig, axes = plt.subplots(4, 1, figsize=(14, 12))
fig.suptitle("VIX vs S&P 500 — Transformatie Analyse", fontsize=14, fontweight="bold")

# Panel 1: Originele Series
ax1 = axes[0]
ax1_twin = ax1.twinx()
ax1.plot(df["date"], df["VIX"], color="#E24B4A", linewidth=1.5, label="VIX")
ax1_twin.plot(df["date"], df["SP500"], color="#378ADD", linewidth=1.5, linestyle="--", label="S&P 500")
ax1.set_ylabel("VIX", color="#E24B4A")
ax1_twin.set_ylabel("S&P 500", color="#378ADD")
ax1.tick_params(axis="y", labelcolor="#E24B4A")
ax1_twin.tick_params(axis="y", labelcolor="#378ADD")
ax1.grid(True, alpha=0.2)
ax1.set_title("Originele Data")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1_twin.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

# Panel 2: VIX vs S&P Rolling Volatility
ax2 = axes[1]
ax2_twin = ax2.twinx()
ax2.plot(df["date"], df["VIX"], color="#E24B4A", linewidth=1.5, label="VIX (Implied Vol)")
ax2_twin.plot(df["date"], df["SP500_RollingVol"], color="#26A65B", linewidth=1.5, label="S&P 500 Realized Vol (20d)")
ax2.set_ylabel("VIX", color="#E24B4A")
ax2_twin.set_ylabel("Realized Volatility (%)", color="#26A65B")
ax2.tick_params(axis="y", labelcolor="#E24B4A")
ax2_twin.tick_params(axis="y", labelcolor="#26A65B")
ax2.grid(True, alpha=0.2)
ax2.set_title("VIX (Implied) vs S&P Realized Volatility")
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

# Panel 3: VIX Z-Score
ax3 = axes[2]
ax3.plot(df["date"], df["VIX_ZScore"], color="#F39C12", linewidth=1.5, label="VIX Z-Score (20d)")
ax3.axhline(y=0, color="gray", linestyle="-", linewidth=0.5, alpha=0.5)
ax3.axhline(y=2, color="red", linestyle="--", linewidth=0.8, alpha=0.5, label="±2σ (Extreme)")
ax3.axhline(y=-2, color="red", linestyle="--", linewidth=0.8, alpha=0.5)
ax3.fill_between(df["date"], -2, 2, alpha=0.1, color="gray")
ax3.set_ylabel("Z-Score", color="#F39C12")
ax3.tick_params(axis="y", labelcolor="#F39C12")
ax3.grid(True, alpha=0.2)
ax3.set_title("VIX Z-Score (Extremes Highlighted)")
ax3.legend(loc="upper left", fontsize=9)

# Panel 4: Rolling Correlation
ax4 = axes[3]
ax4.plot(df["date"], df["VIX_SP500_Corr"], color="#8E44AD", linewidth=1.5, label="Rolling Correlation (20d)")
ax4.axhline(y=0, color="gray", linestyle="-", linewidth=0.5, alpha=0.5)
ax4.axhline(y=corr_global, color="red", linestyle="--", linewidth=1, alpha=0.7, label=f"Global Corr: {corr_global:.2f}")
ax4.fill_between(df["date"], -1, 0, alpha=0.1, color="red", label="Negative Correlation")
ax4.set_ylabel("Correlation", color="#8E44AD")
ax4.set_xlabel("Datum")
ax4.tick_params(axis="y", labelcolor="#8E44AD")
ax4.grid(True, alpha=0.2)
ax4.set_ylim([-1, 1])
ax4.set_title("VIX vs S&P 500 — Rolling Correlation")
ax4.legend(loc="upper left", fontsize=9)

# Format x-axis for all panels
for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

plt.tight_layout()
plt.savefig(DATA_DIR / "vix_snp_analysis.png", dpi=150, bbox_inches="tight")
plt.show()

# ── Statistieken ──────────────────────────────────────────────
print("=" * 60)
print("VIX vs S&P 500 — Transformatie Analyse")
print("=" * 60)
print(f"\n📊 Data Periode: {df['date'].min().date()} - {df['date'].max().date()}")
print(f"📈 Datapunten: {len(df)}")
print(f"\n📉 VIX Statistieken:")
print(f"   Mean: {df['VIX'].mean():.2f}, Std: {df['VIX'].std():.2f}")
print(f"   Min: {df['VIX'].min():.2f}, Max: {df['VIX'].max():.2f}")
print(f"\n📊 S&P 500 Realized Volatility (20d MA):")
print(f"   Mean: {df['SP500_RollingVol'].mean():.2f}%")
print(f"   Range: {df['SP500_RollingVol'].min():.2f}% - {df['SP500_RollingVol'].max():.2f}%")
print(f"\n🔗 Correlaties:")
print(f"   Global: {corr_global:.3f}")
print(f"   Rolling Mean: {df['VIX_SP500_Corr'].mean():.3f}")
print(f"   Range: {df['VIX_SP500_Corr'].min():.3f} - {df['VIX_SP500_Corr'].max():.3f}")
print(f"\n⚠️  Extreme VIX Events (|Z-Score| > 2):")
extreme_events = df[df['VIX_ZScore'].abs() > 2]
print(f"   Aantal: {len(extreme_events)}")
if len(extreme_events) > 0:
    print(f"   Laatse: {extreme_events['date'].iloc[-1].date()}")
print("=" * 60)