import requests
import pandas as pd
from pathlib import Path
from datetime import date

# ── Configuratie ─────────────────────────────────────────────
API_KEY    = "9be0914852d41ae1559bb74f2d4251b4"
DATA_DIR   = Path("data")
CACHE_FILE = DATA_DIR / "vix_historical.csv"

def setup():
    """Maakt data map aan als die nog niet bestaat."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_local() -> pd.DataFrame | None:
    """
    Kijkt of lokale cache bestaat EN van vandaag is.
    - Bestaat niet         → None (ga fetchen)
    - Bestaat maar oud     → None (ga fetchen)
    - Bestaat en up-to-date → geef data terug
    """
    if not CACHE_FILE.exists():
        print("Geen lokaal bestand gevonden, wordt aangemaakt...")
        return None

    df = pd.read_csv(CACHE_FILE, parse_dates=["date"])

    if df.empty:
        print("Lokaal bestand is leeg, wordt opnieuw opgehaald...")
        return None

    laatste_datum = df["date"].max().date()
    vandaag       = date.today()

    if laatste_datum < vandaag:
        print(f"Data verouderd (laatste: {laatste_datum}), wordt bijgewerkt...")
        return None

    print(f"Lokale data is up-to-date: {len(df)} rijen ({df['date'].min().date()} - {laatste_datum})")
    return df

def fetch_fred(series_id: str, start: str = "1990-01-01") -> pd.DataFrame | None:
    """Haalt data op via FRED API. Herbruikbaar voor elke serie."""
    print(f"Ophalen van FRED: {series_id}...")

    response = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id":         series_id,
            "api_key":           API_KEY,
            "file_type":         "json",
            "observation_start": start,
            "sort_order":        "desc"
        }
    )

    if response.status_code != 200:
        print(f"API fout: {response.status_code} - {response.text}")
        return None

    df = pd.DataFrame(response.json()["observations"])[["date", "value"]]
    df = df[df["value"] != "."].copy()
    df["date"]  = pd.to_datetime(df["date"])
    df["value"] = df["value"].astype(float)
    df.rename(columns={"value": series_id}, inplace=True)
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    print(f"Opgehaald: {len(df)} datapunten")
    return df

def save_local(df: pd.DataFrame):
    """Slaat data op als CSV, overschrijft oude versie."""
    df.to_csv(CACHE_FILE, index=False)
    print(f"Opgeslagen: {CACHE_FILE}")

def get_vix() -> pd.DataFrame | None:
    """
    Hoofdfunctie:
    1. Kijk lokaal
    2. Fetch alleen als nodig
    3. Sla automatisch op
    """
    setup()

    # Stap 1: lokale check
    df = load_local()
    if df is not None:
        return df

    # Stap 2: ophalen via API
    df = fetch_fred("VIXCLS")
    if df is None:
        return None

    df.rename(columns={"VIXCLS": "VIX"}, inplace=True)

    # Stap 3: automatisch opslaan
    save_local(df)

    return df

def main():
    df = get_vix()

    if df is None or len(df) < 2:
        print("Onvoldoende data beschikbaar")
        return

    latest   = df.iloc[0]
    previous = df.iloc[1]
    change   = latest["VIX"] - previous["VIX"]

    print(f"\nVIX Overzicht")
    print(f"{'─'*30}")
    print(f"Totaal datapunten : {len(df)}")
    print(f"Periode           : {df['date'].min().date()} - {df['date'].max().date()}")
    print(f"{'─'*30}")
    print(f"Laatste  : {latest['VIX']:.2f}  ({latest['date'].date()})")
    print(f"Vorige   : {previous['VIX']:.2f}  ({previous['date'].date()})")
    print(f"Verschil : {change:+.2f}")
    print(f"\nLaatste 5 dagen:")
    print(df.head(5).to_string(index=False))

if __name__ == "__main__":
    main()