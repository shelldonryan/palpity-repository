import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import get_markets, get_orderbook, save_to_csv
from utils.db_client import save_to_db, init_db
import time
from datetime import datetime

def get_market_info():
    response = get_markets(search="rodovia")
    if not response or not response["data"].get("items"):
        with open("logs.txt", "a") as f:
            f.write(f"[AVISO] Nenhum mercado encontrado. {datetime.now().strftime('%H:%M:%S')}\n")
        return

    market = response["data"]["items"][0]
    market_id = market["id"]

    return (market, market_id)

def get_orderbook_info(market_id):
    orderbook_response = get_orderbook(market_id=market_id)
    if not orderbook_response or not orderbook_response.get("success"):
        with open("logs.txt", "a") as f:
            f.write(f"[AVISO] Orderbook não disponível. {datetime.now().strftime('%H:%M:%S')}\n")
        return

    books = orderbook_response["data"]["books"]
    return books

def collect_orderbook():
    print(f"[INFO] Coletando orderbook... {datetime.now().strftime('%H:%M:%S')}")
    
    (market, market_id) = get_market_info()
    books = get_orderbook_info(market_id)

    for sel in market.get("selections", []):
        selection_id = str(sel["id"])
        name = sel.get("label", "N/A") 
        implied_prob = sel.get("impliedProb", "0.00")

        book = books.get(selection_id, {})
        bids = book.get("bids", [])
        asks = book.get("asks", [])

        first_bid = bids[0] if bids else {"price": "0.00", "amount": "0.00"}
        first_ask = asks[0] if asks else {"price": "0.00", "amount": "0.00"}

        data = {
            "timestamp": datetime.now().isoformat(),
            "marketId": market_id,
            "tag": market.get("tag", "N/A"),
            "selectionId": selection_id,
            "selectionName": name,
            "impliedProb": float(implied_prob),
            "bestBid": float(first_bid["price"]) if bids else 0.0,
            "bestAsk": float(first_ask["price"]) if asks else 0.0,
            "spread": float(first_ask["price"]) - float(first_bid["price"]) if bids and asks else 0.0,
            "bidVolume": float(first_bid["amount"]) if bids else 0.0,
            "askVolume": float(first_ask["amount"]) if asks else 0.0,
            "totalBidVolume": sum(float(b["amount"]) for b in bids),
            "totalAskVolume": sum(float(a["amount"]) for a in asks),
        }

        save_to_db(data)
    else:
        with open("logs.txt", "a") as f:
            f.write(f"[AVISO] Orderbook não disponível. {datetime.now().strftime('%H:%M:%S')}\n")

def main():
    init_db()
    while True:
        collect_orderbook()
        time.sleep(60)

if __name__ == "__main__":
    main()