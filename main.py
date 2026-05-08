from src.Scrapers.fred_scraper import run_scraper as run_fred_scraper
from src.Scrapers.snp500_pipeline import run_scraper as run_snp_scraper
from src.Analysis.vix_zscore_analysis import perform_vix_analysis
from src.Analysis.liquiditeit_roc_analysis import perform_liquiditeit_analysis

def run_task(task_func, task_name):
    """
    Voert een taak uit en rapporteert de status.
    """
    print(f"--- Uitvoeren: {task_name} ---")
    
    try:
        success = task_func()
        if success:
            print(f"Status: {task_name} succesvol afgerond.")
        else:
            print(f"Status: {task_name} mislukt.")
        return success
    except Exception as e:
        print(f"Status: Fout in {task_name}: {e}")
        return False

def main():
    print("========================================")
    print("NOVACAP MACRO ANALYSE PIPELINE")
    print("========================================")

    # Stap 1: Data verzamelen (Scrapers)
    # Deze functies halen de meest recente data op van FRED en Yahoo Finance
    run_task(run_fred_scraper, "FRED Scraper")
    run_task(run_snp_scraper, "S&P 500 Pipeline")

    # Stap 2: Data analyseren (Analysis)
    # Deze functies berekenen de Z-scores en de liquiditeits-correlaties
    run_task(perform_vix_analysis, "VIX Z-Score Analyse")
    
    # Let op: Zorg dat de bestandsnaam hieronder exact klopt met je schijf
    # Als er nog spaties in de naam staan, moet je die hier ook overnemen of de file hernoemen
    run_task(perform_liquiditeit_analysis, "Liquiditeit RoC Analyse")

    print("========================================")
    print("Proces voltooid. Resultaten staan in de map: data/")
    print("========================================")

if __name__ == "__main__":
    main()