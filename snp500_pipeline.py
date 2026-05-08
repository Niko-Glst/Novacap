import os
import time
import requests
import pandas as pd
import yfinance as yf
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
    file_name = "snp500_price_data.csv"
    
    if os.path.exists(file_name):
        print(f"Laden van lokale S&P 500 data...")
        price_data = pd.read_csv(file_name, index_col='Date', parse_dates=True)
    else:
        print(f"Ophalen S&P 500 via Yahoo Finance...")
        asset = yf.Ticker(ticker)
        price_data = asset.history(period="5y", interval="1d")
        price_data.index = price_data.index.tz_localize(None)
        price_data.to_csv(file_name)
        time.sleep(1) # Rate limit protection
        
    return price_data[['Close']].rename(columns={'Close': 'SP500_Close'})

def build_macro_pipeline():
    # 1. Haal data op
    snp500 = get_snp500_data()
    liquidity = get_liquidity_data()
    
    if liquidity is None:
        return

    # 2. Samenvoegen op datum (Inner join zorgt dat we alleen dagen hebben met beide datapunten)
    merged_df = pd.merge(snp500, liquidity, left_index=True, right_index=True, how='inner')
    
    # 3. Voeg de "Forward Return" toe (Wat doet de S&P 500 over 30 dagen?)
    # Dit is wat je uiteindelijk wilt voorspellen.
    merged_df['SP500_Future_30d_Return'] = merged_df['SP500_Close'].shift(-30) / merged_df['SP500_Close'] - 1
    
    # 4. Schoonmaken
    merged_df.dropna(inplace=True)
    
    # Opslaan voor analyse
    merged_df.to_csv("snp500_macro_dataset.csv")
    
    print("\n--- S&P 500 Macro Pijplijn Resultaat ---")
    print(merged_df.tail())
    print("\nDataset opgeslagen als 'snp500_macro_dataset.csv'")

if __name__ == "__main__":
    build_macro_pipeline()