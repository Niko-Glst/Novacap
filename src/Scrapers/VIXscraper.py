import os
import time
import requests
import pandas as pd
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

def get_liquidity_data():
    url = "https://stablecoins.llama.fi/stablecoincharts/all"
    response = requests.get(url).json()
    
    df = pd.DataFrame(response)
    df['date'] = pd.to_datetime(df['date'], unit='s').dt.tz_localize(None)
    df.set_index('date', inplace=True)
    
    df['Total_Liquidity'] = df['totalCirculatingUSD'].apply(
        lambda x: x.get('peggedUSD') if isinstance(x, dict) else None
    )
    df['Liquidity_30d_RoC'] = df['Total_Liquidity'].pct_change(periods=30)
    
    return df[['Total_Liquidity', 'Liquidity_30d_RoC']]

def get_price_data(ticker="BTC-USD"):
    file_name = f"{ticker}_price_data.csv"
    
    # 1. Controleer lokaal bestand (Cache check)
    if os.path.exists(file_name):
        print(f"Laden van lokale data voor {ticker} (API bespaard).")
        price_data = pd.read_csv(file_name, index_col='Date', parse_dates=True)
        return price_data[['Close']]
        
    # 2. Ophalen via API indien bestand niet bestaat
    print(f"Ophalen van nieuwe API data voor {ticker}...")
    asset = yf.Ticker(ticker)
    price_data = asset.history(period="2y", interval="1d")
    price_data.index = price_data.index.tz_localize(None)
    
    # 3. Data direct opslaan voor toekomstig gebruik
    price_data.to_csv(file_name)
    print(f"Data opgeslagen als {file_name}.")
    
    # 4. Rate-limit bescherming (pauzeer 1 seconde)
    time.sleep(1)
    
    return price_data[['Close']]

def build_pipeline():
    liquidity = get_liquidity_data()
    price = get_price_data("BTC-USD")
    
    merged_df = pd.merge(price, liquidity, left_index=True, right_index=True, how='inner')
    merged_df.rename(columns={'Close': 'BTC_Price'}, inplace=True)
    
    merged_df['BTC_Future_14d_Return'] = merged_df['BTC_Price'].shift(-14) / merged_df['BTC_Price'] - 1
    merged_df.dropna(inplace=True)
    
    display_df = merged_df.tail().copy()
    display_df['Liquidity_30d_RoC'] = display_df['Liquidity_30d_RoC'].map("{:.2%}".format)
    display_df['BTC_Future_14d_Return'] = display_df['BTC_Future_14d_Return'].map("{:.2%}".format)
    
    print("\nPipeline Data (Laatste 5 meetbare dagen):")
    print(display_df[['BTC_Price', 'Liquidity_30d_RoC', 'BTC_Future_14d_Return']])
    
    merged_df.to_csv("macro_signal_dataset.csv")

if __name__ == "__main__":
    build_pipeline()