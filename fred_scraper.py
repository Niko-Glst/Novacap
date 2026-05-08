import asyncio
import re
import pandas as pd
from pathlib import Path
from crawl4ai import AsyncWebCrawler

DATA_DIR   = Path("data")
CACHE_FILE = DATA_DIR / "vix_historical.csv"
URL        = "https://fred.stlouisfed.org/data/VIXCLS.txt"

def load_local() -> pd.DataFrame | None:
    if CACHE_FILE.exists():
        df = pd.read_csv(CACHE_FILE, parse_dates=["date"])
        print(f"Lokale data gevonden: {len(df)} rijen ({df['date'].min().date()} - {df['date'].max().date()})")
        return df
    print("Geen lokale data gevonden, wordt opgehaald...")
    return None

async def scrape_vix() -> pd.DataFrame | None:
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=URL, bypass_cache=True)

        if not result.success:
            print(f"Ophalen mislukt: {result.error_message}")
            return None

        # Probeer html attribuut ipv markdown — bevat ruwe tekstdata
        raw = result.html

        print("--- RAW OUTPUT (eerste 300 tekens) ---")
        print(repr(raw[:300]))
        print("--- EINDE DEBUG ---")

        # FRED .txt formaat: "1990-01-02  23.34"
        pattern = r"(\d{4}-\d{2}-\d{2})\s+([\d.]+)"
        matches = re.findall(pattern, raw)
        print(f"Matches gevonden: {len(matches)}")

        if not matches:
            print("Geen data gevonden")
            return None

        df = pd.DataFrame(matches, columns=["date", "VIX"])
        df["date"] = pd.to_datetime(df["date"])
        df["VIX"]  = df["VIX"].astype(float)
        df = df.sort_values("date", ascending=False).reset_index(drop=True)
        return df

async def get_vix(force_refresh: bool = False) -> pd.DataFrame | None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not force_refresh:
        df = load_local()
        if df is not None:
            return df

    df = await scrape_vix()

    if df is not None:
        df.to_csv(CACHE_FILE, index=False)
        print(f"Opgeslagen: {CACHE_FILE}")

    return df

async def main():
    # Verwijder oude cache eerst: del data\vix_historical.csv
    df = await get_vix(force_refresh=True)

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
    asyncio.run(main())