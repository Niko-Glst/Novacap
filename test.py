import requests
import pandas as pd

# 1. Definieer de databron (DefiLlama Stablecoin API)
url = "https://stablecoins.llama.fi/stablecoincharts/all"

print("📡 Data ophalen van DefiLlama...")

# 2. Stuur een verzoek naar de website
response = requests.get(url)

# 3. Controleer of we succesvol data hebben gekregen (Status 200 = OK)
if response.status_code == 200:
    # Haal de ruwe JSON data uit het antwoord
    raw_data = response.json()
    
    # 4. Stop de data in een Pandas DataFrame (een soort Excel-tabel in Python)
    df = pd.DataFrame(raw_data)
    
    # 5. Maak de datums leesbaar (ze komen binnen als computertijd/Unix)
    df['date'] = pd.to_datetime(df['date'], unit='s')
    
    # We selecteren alleen de datum en de totale liquiditeit in dollars
    df_clean = df[['date', 'totalCirculatingUSD']]
    
    # 6. Print de laatste 5 dagen op het scherm
    print("\n✅ Succes! Hier is de macro-liquiditeit van de afgelopen 5 dagen:")
    print(df_clean.tail())

else:
    print(f"❌ Er ging iets mis. Foutcode: {response.status_code}")