# scripts/collector.py
from utils.api_client import get_orderbook, get_market, save_to_csv
import time
from datetime import datetime

# ID do seu mercado de rodovia (exemplo: 123)
MARKET_ID = 123  # Substitua pelo ID real do mercado "Quantos carros?"

def collect_orderbook():
    print(f"[INFO] Coletando orderbook... {datetime.now().strftime('%H:%M:%S')}")
    orderbook = get_orderbook(market_id=MARKET_ID)
    if orderbook:
        # Extrai dados relevantes
        market_id = orderbook.get("marketId")
        selections = orderbook.get("selections", [])
        for sel in selections:
            selection_id = sel.get("selectionId")
            name = sel.get("name")
            bids = sel.get("bids", [])
            asks = sel.get("asks", [])
            # Salva o primeiro bid e ask como exemplo
            first_bid = bids if bids else {"price": "0.00", "quantity": "0.00"}
            first_ask = asks if asks else {"price": "0.00", "quantity": "0.00"}
            data = {
                "timestamp": datetime.now().isoformat(),
                "marketId": market_id,
                "selectionId": selection_id,
                "selectionName": name,
                "bidPrice": first_bid["price"],
                "bidQuantity": first_bid["quantity"],
                "askPrice": first_ask["price"],
                "askQuantity": first_ask["quantity"]
            }
            save_to_csv(data)
    else:
        print("[AVISO] Orderbook não disponível.")

def main():
    while True:
        collect_orderbook()
        time.sleep(300)  # Espera 5 minutos entre rodadas

if __name__ == "__main__":
    main()