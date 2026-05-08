import json
import os
import time
import requests
import pandas as pd
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings('ignore')

STATUS_FILE = "data/status.json"


def load_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_status(data):
    status = load_status()
    status.update(data)
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

def get_liquidity_data():
    """Haalt stablecoin liquiditeit op van DeFiLlama met verbeterde datumverwerking."""
    url = "https://stablecoins.llama.fi/stablecoincharts/all"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise error for bad status
        data = response.json()
        df = pd.DataFrame(data)
        
        # Verbeterde datumconversie: we dwingen het naar numeriek en dan naar datetime
        df['date'] = pd.to_numeric(df['date'], errors='coerce')
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
    except requests.RequestException as e:
        print(f"Fout bij ophalen van liquiditeitsdata: {e}")
        return None
    except Exception as e:
        print(f"Onverwachte fout bij verwerken van liquiditeitsdata: {e}")
        return None

def get_snp500_data():
    """Haalt S&P 500 data op met lokale caching."""
    ticker = "^GSPC"  # S&P 500 Index
    file_name = "data/snp500_price_data.csv"
    
    # Eerst lokale cache bekijken
    if os.path.exists(file_name):
        try:
            print("Laden van lokale S&P 500 data...")
            price_data = pd.read_csv(file_name, index_col='Date', parse_dates=True)
            return price_data[['Close']].rename(columns={'Close': 'SP500_Close'})
        except Exception as e:
            print(f"Fout bij laden van lokale S&P 500 data: {e}. Er wordt opnieuw opgehaald.")

    # Ophalen als er geen lokale data is of als laden faalt
    print(f"Ophalen van S&P 500 via Yahoo Finance...")
    try:
        asset = yf.Ticker(ticker)
        price_data = asset.history(period="max", interval="1d")
        price_data.index = price_data.index.tz_localize(None)
        price_data.to_csv(file_name)
        time.sleep(1)  # Rate limit protection
        return price_data[['Close']].rename(columns={'Close': 'SP500_Close'})
    except Exception as e:
        print(f"Fout bij ophalen van S&P 500 data: {e}")
        return None

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
    os.makedirs("data", exist_ok=True)
    merged_df.to_csv("data/snp500_macro_dataset.csv")
    
    latest = merged_df.iloc[-1]
    status_update = {
        "sp500": {
            "last_date": latest.name.strftime("%Y-%m-%d"),
            "close": float(latest['SP500_Close']),
            "change_30d_pct": float((latest['SP500_Close'] / merged_df['SP500_Close'].iloc[-31] - 1) * 100) if len(merged_df) > 30 else None,
            "trend": "Up" if len(merged_df) > 30 and latest['SP500_Close'] > merged_df['SP500_Close'].iloc[-31] else "Down"
        },
        "liquidity": {
            "last_date": latest.name.strftime("%Y-%m-%d"),
            "roc_30d_pct": float(latest['Liquidity_30d_RoC'] * 100) if pd.notna(latest['Liquidity_30d_RoC']) else None
        },
        "updated": pd.Timestamp.now().isoformat()
    }
    save_status(status_update)
    
    print("\n--- S&P 500 Macro Pijplijn Resultaat ---")
    print(merged_df.tail())
    print("\nDataset opgeslagen als 'data/snp500_macro_dataset.csv'")

def run_scraper():
    """Hoofdfunctie om de S&P 500 pipeline te runnen."""
    try:
        build_macro_pipeline()
        print("S&P 500 scraper: Succesvol")
        return True
    except Exception as e:
        print(f"S&P 500 scraper: Fout opgetreden: {e}")
        return False

if __name__ == "__main__":
    run_scraper()