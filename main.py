import subprocess
import sys
import os

def run_script(script_path):
    """
    Voert een Python script uit en rapporteert de status.
    """
    print(f"--- Uitvoeren: {script_path} ---")
    
    # Gebruik het absolute pad om fouten met werkmappen te voorkomen
    abs_path = os.path.abspath(script_path)
    
    # Controleer of het bestand bestaat voordat we het uitvoeren
    if not os.path.exists(abs_path):
        print(f"Fout: Bestand niet gevonden op {abs_path}")
        return

    result = subprocess.run([sys.executable, abs_path], capture_output=False)
    
    if result.returncode == 0:
        print(f"Status: {os.path.basename(script_path)} succesvol afgerond.")
    else:
        print(f"Status: Fout opgetreden in {os.path.basename(script_path)}.")

def main():
    print("========================================")
    print("NOVACAP MACRO ANALYSE PIPELINE")
    print("========================================")

    # Stap 1: Data verzamelen (Scrapers)
    # Deze scripts halen de meest recente data op van FRED en Yahoo Finance
    run_script("src/Scrapers/fred_scraper.py")
    run_script("src/Scrapers/snp500_pipeline.py")

    # Stap 2: Data analyseren (Analysis)
    # Deze scripts berekenen de Z-scores en de liquiditeits-correlaties
    run_script("src/Analysis/vix_zscore_analysis.py")
    
    # Let op: Zorg dat de bestandsnaam hieronder exact klopt met je schijf
    # Als er nog spaties in de naam staan, moet je die hier ook overnemen of de file hernoemen
    run_script("src/Analysis/liquiditeit_roc_analysis.py")

    print("========================================")
    print("Proces voltooid. Resultaten staan in de map: data/")
    print("========================================")

if __name__ == "__main__":
    main()