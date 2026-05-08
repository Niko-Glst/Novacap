import pandas as pd
import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Laad environment variables uit .env bestand
load_dotenv()

# Geen LLM nodig, we gebruiken regel-gebaseerd advies

def load_data():
    """Laad de opgeslagen CSV data."""
    try:
        # Laad S&P 500 data
        snp_df = pd.read_csv("data/snp500_price_data.csv", index_col='Date', parse_dates=True)
        snp_df = snp_df[['Close']].rename(columns={'Close': 'SP500_Close'})
        
        # Laad VIX data
        vix_df = pd.read_csv("data/vix_historical.csv", index_col='date', parse_dates=True)
        vix_df.rename(columns={'value': 'VIX'}, inplace=True)
        vix_df['VIX'] = pd.to_numeric(vix_df['VIX'], errors='coerce')
        
        # Merge op datum (inner join voor gemeenschappelijke datums)
        df = pd.merge(snp_df, vix_df, left_index=True, right_index=True, how='inner')
        
        return df
    except FileNotFoundError as e:
        print(f"Fout bij laden data: {e}")
        return None

def compute_metrics(df):
    """Bereken relevante metrics voor advies."""
    if df.empty:
        return None
    
    # Neem de laatste beschikbare data
    latest = df.iloc[-1]
    
    # Bereken VIX Z-score (rolling 252 dagen)
    window = 252
    df['VIX_Mean'] = df['VIX'].rolling(window=window).mean()
    df['VIX_Std'] = df['VIX'].rolling(window=window).std()
    df['VIX_ZScore'] = (df['VIX'] - df['VIX_Mean']) / df['VIX_Std']
    
    latest_zscore = df['VIX_ZScore'].iloc[-1]
    
    # Recente verandering S&P 500 (laatste 30 dagen)
    sp_change_30d = (latest['SP500_Close'] / df['SP500_Close'].iloc[-30] - 1) * 100 if len(df) > 30 else 0
    
    # VIX verandering
    vix_change_30d = (latest['VIX'] / df['VIX'].iloc[-30] - 1) * 100 if len(df) > 30 else 0
    
    metrics = {
        "current_sp500": latest['SP500_Close'],
        "current_vix": latest['VIX'],
        "vix_zscore": latest_zscore,
        "sp500_change_30d": sp_change_30d,
        "vix_change_30d": vix_change_30d,
        "liquidity_roc": latest.get('Liquidity_30d_RoC', 0) * 100
    }
    
    return metrics

def get_llm_advice(metrics):
    """Geef eenvoudig advies gebaseerd op metrics (zonder LLM)."""
    zscore = metrics['vix_zscore']
    sp_change = metrics['sp500_change_30d']
    vix_change = metrics['vix_change_30d']
    current_vix = metrics['current_vix']
    
    reasons = []
    
    if zscore > 1:
        reasons.append("Hoge VIX Z-score duidt op verhoogde marktspanning en risico.")
    elif zscore < -1:
        reasons.append("Lage VIX Z-score suggereert markt euforie en kalmte.")
    
    if sp_change > 5:
        reasons.append("S&P 500 is sterk gestegen, bullish momentum.")
    elif sp_change < -5:
        reasons.append("S&P 500 is gedaald, bearish signaal.")
    
    if vix_change < -10:
        reasons.append("VIX daalt sterk, angst neemt af.")
    elif vix_change > 10:
        reasons.append("VIX stijgt, angst neemt toe.")
    
    if current_vix < 15:
        reasons.append("VIX laag, markt kalm.")
    elif current_vix > 25:
        reasons.append("VIX hoog, hoge volatiliteit.")
    
    # Combineer tot advies
    if zscore > 1 or sp_change < -5 or vix_change > 10 or current_vix > 25:
        advice = "Voorzichtig: " + "; ".join(reasons) + ". Niet ideaal om nu in te stappen."
    elif zscore < -1 or sp_change > 5 or vix_change < -10 or current_vix < 15:
        advice = "Goed moment: " + "; ".join(reasons) + ". Overweeg in te stappen."
    else:
        advice = "Neutraal: " + "; ".join(reasons) + ". Houd markt in de gaten."
    
    return advice

def plot_data(df, days):
    """Plot VIX en S&P 500 voor de laatste 'days' dagen."""
    if df.empty:
        print("Geen data om te plotten.")
        return
    
    # Neem laatste 'days' dagen
    recent_df = df.tail(days)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # S&P 500
    ax1.plot(recent_df.index, recent_df['SP500_Close'], color='blue', label='S&P 500')
    ax1.set_ylabel('S&P 500 Prijs', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    
    # VIX op tweede as
    ax2 = ax1.twinx()
    ax2.plot(recent_df.index, recent_df['VIX'], color='red', label='VIX')
    ax2.set_ylabel('VIX Niveau', color='red')
    ax2.tick_params(axis='y', labelcolor='red')
    
    # Titel en legenda
    ax1.set_title(f'VIX vs S&P 500 - Laatste {days} dagen')
    fig.tight_layout()
    plt.show()

def main():
    print("=== Markt Advies Agent ===")
    
    # Laad data
    df = load_data()
    if df is None:
        return
    
    # Bereken metrics
    metrics = compute_metrics(df)
    if metrics is None:
        print("Geen data beschikbaar voor analyse.")
        return
    
    print("Data geladen en metrics berekend.")
    
    # Hele analyse
    print("\n--- Volledige Markt Analyse ---")
    print(f"Huidige S&P 500 prijs: {metrics['current_sp500']:.2f}")
    print(f"  - Dit is de laatste beschikbare slotprijs van de S&P 500 index.")
    print(f"Huidige VIX niveau: {metrics['current_vix']:.2f}")
    print(f"  - VIX is uitgedrukt in procentpunten (index van 0-100+). Meet verwachte marktvolatiliteit over 30 dagen.")
    print(f"    - < 15: Lage angst, markt kalm/euforisch (goed voor instappen).")
    print(f"    - 15-20: Normaal niveau.")
    print(f"    - > 25: Hoge angst/volatiliteit (voorzichtig, mogelijk correctie).")
    print(f"VIX Z-score: {metrics['vix_zscore']:.2f}")
    if metrics['vix_zscore'] > 1:
        print("  - Z-score > 1: VIX hoger dan gemiddeld afgelopen jaar, verhoogde spanning. Slecht moment om in te stappen.")
    elif metrics['vix_zscore'] < -1:
        print("  - Z-score < -1: VIX lager dan gemiddeld, markt euforisch. Goed moment voor risicovolle trades.")
    else:
        print("  - Z-score tussen -1 en 1: VIX normaal. Neutraal signaal.")
    print(f"S&P 500 verandering afgelopen 30 dagen: {metrics['sp500_change_30d']:.2f}%")
    if metrics['sp500_change_30d'] > 0:
        print("  - Positieve verandering: Markt momentum omhoog, bullish signaal voor instappen.")
    else:
        print("  - Negatieve verandering: Markt daalt, bearish. Wacht op omkeer voordat instappen.")
    print(f"VIX verandering afgelopen 30 dagen: {metrics['vix_change_30d']:.2f}%")
    print("  - Negatieve verandering (zoals nu) betekent angst neemt af, markt wordt kalmer. Positief voor instappen.")
    print("  - Positieve verandering: Angst neemt toe, volatiliteit hoger. Voorzichtig zijn.")
    print(f"Liquiditeit Rate of Change: {metrics.get('liquidity_roc', 'N/A')}%")
    if pd.isna(metrics.get('liquidity_roc')) or metrics.get('liquidity_roc') == 0:
        print("  - Niet beschikbaar in huidige data. Meet verandering in crypto-liquiditeit over 30 dagen.")
        print("    - Positief: Meer liquiditeit, bullish voor risk assets.")
        print("    - Negatief: Minder liquiditeit, bearish signaal.")
    else:
        roc = metrics['liquidity_roc']
        print(f"  - Verandering in crypto-liquiditeit: {roc:.2f}%. Positief = meer liquiditeit, bullish; negatief = bearish.")
    
    # Kort advies
    advice = get_llm_advice(metrics)
    
    print("\n--- Kort Advies ---")
    print(advice)
    
    # Optie om grafiek te bekijken
    plot_choice = input("\nWil je de VIX en S&P 500 grafiek bekijken? (ja/nee): ").strip().lower()
    if plot_choice == 'ja':
        period_choice = input("Kies periode: 30 dagen of 3 maanden (30/90): ").strip()
        if period_choice == '30':
            days = 30
        elif period_choice == '90':
            days = 90
        else:
            print("Ongeldige keuze, standaard 30 dagen.")
            days = 30
        plot_data(df, days)

if __name__ == "__main__":
    main()