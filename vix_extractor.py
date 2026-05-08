import pandas as pd
import re

def extract_vix_from_md(file_path="vix_raw_data.md"):
    print(f"Extraheren van VIX data uit {file_path}...")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Nieuw patroon: Zoekt naar 'YYYY-MM-DD:' gevolgd door een getal
        # Voorbeeld in jouw tekst: 2026-05-01: 16.99
        pattern = r"(\d{4}-\d{2}-\d{2}):\s+(\d+\.\d+)"
        matches = re.findall(pattern, content)

        if not matches:
            print("FOUT: Geen data gevonden. De structuur van de tekst is anders dan verwacht.")
            # Print een klein stukje van de tekst om te debuggen
            return None

        # Maak DataFrame
        vix_df = pd.DataFrame(matches, columns=['Date', 'VIX_Close'])
        vix_df['Date'] = pd.to_datetime(vix_df['Date'])
        vix_df['VIX_Close'] = pd.to_numeric(vix_df['VIX_Close'])
        
        # Sorteer op datum (oud naar nieuw)
        vix_df = vix_df.sort_values('Date')
        vix_df.set_index('Date', inplace=True)
        
        print(f"Succes! {len(vix_df)} unieke VIX-datums gevonden.")
        return vix_df

    except FileNotFoundError:
        print(f"Bestand {file_path} niet gevonden.")
        return None

if __name__ == "__main__":
    vix_data = extract_vix_from_md()
    if vix_data is not None:
        print("\nGeëxtraheerde VIX waarden:")
        print(vix_data)