import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_markets
from utils.db_client import save_result, init_results_table
import time
from datetime import datetime
from config import API_BASE_URL

def extract_result_info(market):
    """Extrai informações relevantes do mercado resolvido."""
    market_id = market.get("id")
    result_selection_id = market.get("resultSelectionId")
    resolved_at = market.get("resolvedAt")
    value_needed = market.get("valueNeeded")
    tag = market.get("tag", "UNKNOWN")
    
    result_name = None
    prob_winner = None
    prob_loser = None
    
    for sel in market.get("selections", []):
        if sel.get("id") == result_selection_id:
            result_name = sel.get("label")
            prob_winner = float(sel.get("impliedProb", 0))
        else:
            prob_loser = float(sel.get("impliedProb", 0))
    
    return {
        "marketId": market_id,
        "tag": tag,
        "threshold": value_needed,
        "resultSelectionId": result_selection_id,
        "resultName": result_name,
        "probWinner": prob_winner,
        "probLoser": prob_loser,
        "resolvedAt": resolved_at
    }

def collect_recent_results():
    """Coleta resultados dos mercados resolvidos recentemente."""
    print(f"[INFO] Coletando resultados... {datetime.now().strftime('%H:%M:%S')}")
    
    response = get_markets(search="rodovia", orderDirection="DESC", status="RESOLVED", limit=2)

    if not response.get("success"):
        print("[ERRO] Falha na requisição.")
        return
    
    if not response or not response.get("data", {}).get("items"):
        print("[AVISO] Nenhum mercado resolvido encontrado.")
        return
    
    for market in response.get("data", {}).get("items", []):
        result_info = extract_result_info(market)
        save_result(result_info)

def main():
    init_results_table()
    while True:
        collect_recent_results()
        time.sleep(240)

if __name__ == "__main__":
    main()