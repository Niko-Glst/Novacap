import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def perform_vix_analysis():
    # 1. Data inladen
    # Zorg dat de bestandsnamen kloppen met wat je eerder hebt opgeslagen
    try:
        snp = pd.read_csv("data/snp500_macro_dataset.csv", index_col='Date', parse_dates=True)
        vix = pd.read_csv("data/vix_historical.csv", index_col='date', parse_dates=True)
    except FileNotFoundError:
        print("Fout: Kon de CSV bestanden niet vinden in de map.")
        return

    # 2. Mergen
    df = pd.merge(snp, vix, left_index=True, right_index=True, how='inner')
    df.rename(columns={'value': 'VIX'}, inplace=True)
    df['VIX'] = pd.to_numeric(df['VIX'], errors='coerce')

    # 3. Z-Score berekenen (Rolling 252 days = 1 jaar aan beursdagen)
    window = 252
    df['VIX_Mean'] = df['VIX'].rolling(window=window).mean()
    df['VIX_Std'] = df['VIX'].rolling(window=window).std()
    df['VIX_ZScore'] = (df['VIX'] - df['VIX_Mean']) / df['VIX_Std']

    # 4. Visualisatie
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # Subplot 1: S&P 500 Prijs
    ax1.plot(df.index, df['SP500_Close'], color='blue', label='S&P 500')
    ax1.set_title('S&P 500 Prijsverloop')
    ax1.legend()

    # Subplot 2: VIX Z-Score
    ax2.plot(df.index, df['VIX_ZScore'], color='red', label='VIX Z-Score (1Y Rolling)')
    ax2.axhline(y=2, color='black', linestyle='--', label='Extreme Angst (+2)')
    ax2.axhline(y=-2, color='black', linestyle='--', label='Extreme Euforie (-2)')
    ax2.fill_between(df.index, 0, df['VIX_ZScore'], where=(df['VIX_ZScore'] >= 0), color='red', alpha=0.3)
    ax2.fill_between(df.index, 0, df['VIX_ZScore'], where=(df['VIX_ZScore'] < 0), color='green', alpha=0.3)
    ax2.set_title('VIX Z-Score (Sentiment Indicator)')
    ax2.legend()

    plt.tight_layout()
    plt.savefig("data/vix_zscore_analysis.png")
    print("Analyse voltooid! Grafiek opgeslagen als 'data/vix_zscore_analysis.png'")
    plt.show()
    
    return True

    # 5. Correlatie check
    correlation = df['VIX_ZScore'].corr(df['SP500_Future_30d_Return'])
    print(f"Correlatie tussen VIX Z-Score en toekomstig rendement: {correlation:.2f}")

if __name__ == "__main__":
    perform_vix_analysis()