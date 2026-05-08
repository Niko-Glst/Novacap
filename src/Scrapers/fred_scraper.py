import json
import requests
import pandas as pd
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
import os

# Laad environment variables
load_dotenv()

# ── Configuratie ─────────────────────────────────────────────
API_KEY    = os.getenv("FRED_API_KEY")
DATA_DIR   = Path("data")
CACHE_FILE = DATA_DIR / "vix_historical.csv"
STATUS_FILE = DATA_DIR / "status.json"


def load_status() -> dict:
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_status(data: dict):
    status = load_status()
    status.update(data)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

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
    
    try:
        response = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id":         series_id,
                "api_key":           API_KEY,
                "file_type":         "json",
                "observation_start": start,
                "sort_order":        "desc"
            },
            timeout=10  # Timeout om te voorkomen dat het vastloopt
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
    except requests.RequestException as e:
        print(f"Netwerkfout bij ophalen van {series_id}: {e}")
        return None
    except Exception as e:
        print(f"Onverwachte fout bij ophalen van {series_id}: {e}")
        return None

def save_local(df: pd.DataFrame):
    """Slaat data op als CSV, overschrijft oude versie."""
    df.to_csv(CACHE_FILE, index=False)
    print(f"Opgeslagen: {CACHE_FILE}")


def save_vix_status(df: pd.DataFrame):
    """Werk de status.json bij met de meest recente VIX metrics."""
    if df.empty:
        return

    df_asc = df.sort_values("date", ascending=True).reset_index(drop=True)
    latest = df_asc.iloc[-1]
    change_30d = None
    if len(df_asc) > 30:
        change_30d = float((latest['VIX'] / df_asc['VIX'].iloc[-31] - 1) * 100)

    trend = 'Up' if len(df_asc) > 1 and latest['VIX'] > df_asc['VIX'].iloc[-2] else 'Down'
    vix_status = {
        "vix": {
            "last_date": latest['date'].strftime("%Y-%m-%d"),
            "value": float(latest['VIX']),
            "change_30d_pct": change_30d,
            "trend": trend,
            "zscore": None
        }
    }

    if len(df_asc) >= 252:
        rolling = df_asc['VIX'].rolling(window=252)
        mean = rolling.mean().iloc[-1]
        std = rolling.std().iloc[-1]
        if std and not pd.isna(mean):
            vix_status['vix']['zscore'] = float((latest['VIX'] - mean) / std)

    save_status(vix_status)

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
        save_vix_status(df)
        return df

    # Stap 2: ophalen via API
    df = fetch_fred("VIXCLS")
    if df is None:
        return None

    df.rename(columns={"VIXCLS": "VIX"}, inplace=True)

    # Stap 3: automatisch opslaan
    save_local(df)
    save_vix_status(df)

    return df

def run_scraper():
    """Hoofdfunctie om de scraper te runnen."""
    df = get_vix()
    
    if df is None or len(df) < 2:
        print("FRED scraper: Onvoldoende data beschikbaar")
        return False
    
    latest   = df.iloc[0]
    previous = df.iloc[1]
    change   = latest["VIX"] - previous["VIX"]
    
    print(f"\nVIX Overzicht")
    print(f"{'─'*30}")
    print(f"Totaal datapunten : {len(df)}")
    print(f"Laatste waarde    : {latest['VIX']:.2f} ({latest['date'].date()})")
    print(f"Verandering       : {change:+.2f}")
    print(f"Status            : Succesvol")
    return True

def main():
    run_scraper()

if __name__ == "__main__":
    main()