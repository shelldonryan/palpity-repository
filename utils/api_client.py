import requests
import base64
from config import API_BASE_URL, API_KEY, API_SECRET

def get_bearer_token():
    token = base64.b64encode(f"{API_KEY}:{API_SECRET}".encode()).decode()
    return f"Bearer {token}"

def get_headers():
    return {
        "Authorization": get_bearer_token(),
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def get_market(market_id):
    url = f"{API_BASE_URL}/markets/{market_id}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERRO] Falha ao buscar mercado {market_id}: {e}")
        return None

def get_orderbook(market_id=None, selection_id=None, limit=50):
    url = f"{API_BASE_URL}/orderbook"
    params = {}
    if market_id:
        params["marketId"] = market_id
    if selection_id:
        params["selectionId"] = selection_id
    if limit:
        params["limit"] = limit

    try:
        response = requests.get(url, headers=get_headers(), params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERRO] Falha ao buscar orderbook: {e}")
        return None

def save_to_csv(data, filename="data/raw_data.csv"):
    import pandas as pd
    df = pd.DataFrame([data])
    df.to_csv(filename, mode='a', header=False, index=False)
    print(f"[INFO] Dados salvos: {data.get('marketId', 'N/A')}")