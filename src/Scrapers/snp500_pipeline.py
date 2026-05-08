import os
import time
import requests
import pandas as pd
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def get_liquidity_data():
    """Haalt stablecoin liquiditeit op van DeFiLlama met verbeterde datumverwerking."""
    url = "https://stablecoins.llama.fi/stablecoincharts/all"
    try:
        response = requests.get(url).json()
        df = pd.DataFrame(response)
        
        # Verbeterde datumconversie: we dwingen het naar numeriek en dan naar datetime
        df['date'] = pd.to_numeric(df['date'])
        df['date'] = pd.to_datetime(df['date'], unit='s', errors='coerce')
        
        # Verwijder tijdzones en eventuele ongeldige datums
        df['date'] = df['date'].dt.tz_localize(None)
        df = df.dropna(subset=['date'])
        
        df.set_index('date', inplace=True)
        
        # Extract de USD waarde uit de dictionary kolom
        df['Total_Liquidity'] = df['totalCirculatingUSD'].apply(
            lambda x: x.get('peggedUSD') if isinstance(x, dict) else None
        )
        
        # Sorteer op datum om RoC (Rate of Change) correct te berekenen
        df = df.sort_index()
        df['Liquidity_30d_RoC'] = df['Total_Liquidity'].pct_change(periods=30)
        
        return df[['Total_Liquidity', 'Liquidity_30d_RoC']]
    except Exception as e:
        print(f"Fout bij DeFiLlama: {e}")
        return None

def get_snp500_data():
    """Haalt S&P 500 data op met lokale caching."""
    ticker = "^GSPC"  # S&P 500 Index
    file_name = "data/snp500_price_data.csv"
    
    # Altijd verse data ophalen voor testen
    print(f"Ophalen verse S&P 500 via Yahoo Finance...")
    asset = yf.Ticker(ticker)
    price_data = asset.history(period="max", interval="1d")
    price_data.index = price_data.index.tz_localize(None)
    price_data.to_csv(file_name)
    time.sleep(1) # Rate limit protection
        
    return price_data[['Close']].rename(columns={'Close': 'SP500_Close'})

def build_macro_pipeline():
    # 1. Haal data op
    snp500 = get_snp500_data()
    liquidity = get_liquidity_data()
    
    # Als liquidity niet beschikbaar, ga door met NaN
    if liquidity is None:
        liquidity = pd.DataFrame(index=snp500.index)
        liquidity['Total_Liquidity'] = np.nan
        liquidity['Liquidity_30d_RoC'] = np.nan

    # 2. Samenvoegen op datum (Left join zodat alle S&P data behouden blijft)
    merged_df = pd.merge(snp500, liquidity, left_index=True, right_index=True, how='left')
    
    # Vul ontbrekende liquiditeit met NaN
    if 'Total_Liquidity' not in merged_df.columns:
        merged_df['Total_Liquidity'] = np.nan
        merged_df['Liquidity_30d_RoC'] = np.nan
    
    # Vul ontbrekende liquiditeit met NaN
    if 'Total_Liquidity' not in merged_df.columns:
        merged_df['Total_Liquidity'] = np.nan
        merged_df['Liquidity_30d_RoC'] = np.nan
    
    # 3. Voeg de "Forward Return" toe (Wat doet de S&P 500 over 30 dagen?)
    # Dit is wat je uiteindelijk wilt voorspellen.
    merged_df['SP500_Future_30d_Return'] = merged_df['SP500_Close'].shift(-30) / merged_df['SP500_Close'] - 1
    
    # 4. Schoonmaken - alleen NaN in SP500_Close verwijderen
    merged_df.dropna(subset=['SP500_Close'], inplace=True)
    
    # Opslaan voor analyse
    merged_df.to_csv("data/snp500_macro_dataset.csv")
    
    print("\n--- S&P 500 Macro Pijplijn Resultaat ---")
    print(merged_df.tail())
    print("\nDataset opgeslagen als 'data/snp500_macro_dataset.csv'")

if __name__ == "__main__":
    build_macro_pipeline()