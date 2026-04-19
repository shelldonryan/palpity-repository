import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import sqlite3
from datetime import datetime
import os

API_URL = "https://palpity-repository.onrender.com/data"
DB_PATH = "./data/palpity.db"
SYNC_FILE = "./data/last_sync.txt"


# =========================
# LAST SYNC
# =========================
def get_last_sync():
    if not os.path.exists(SYNC_FILE):
        return None

    with open(SYNC_FILE, "r") as f:
        return f.read().strip()


def save_last_sync():
    with open(SYNC_FILE, "w") as f:
        f.write(datetime.utcnow().isoformat())


# =========================
# FETCH
# =========================
def fetch_data():
    since = get_last_sync()

    try:
        url = API_URL
        if since:
            url += f"?since={since}"

        print(f"Buscando desde: {since}")

        r = requests.get(url, timeout=15)
        r.raise_for_status()

        return r.json()

    except Exception as e:
        print("Erro:", e)
        return None


# =========================
# DB
# =========================
def get_conn():
    return sqlite3.connect(DB_PATH)


# =========================
# ROUND RESULTS
# =========================
def insert_round_results(rows):
    conn = get_conn()
    cursor = conn.cursor()

    inserted = 0

    for r in rows:
        try:
            cursor.execute("""
                INSERT INTO round_results (
                    marketId,
                    tag,
                    threshold,
                    resultSelectionId,
                    resultSelectionName,
                    impliedProbWinner,
                    impliedProbLoser,
                    resolvedAt,
                    createdAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r[1],  # marketId
                r[2],  # tag
                r[3],  # threshold
                r[4],  # resultSelectionId
                r[5],  # resultSelectionName
                r[6],  # impliedProbWinner
                r[7],  # impliedProbLoser
                r[8],  # resolvedAt
                r[9],  # createdAt
            ))

            inserted += 1

        except sqlite3.IntegrityError:
            # já existe (UNIQUE marketId)
            pass

    conn.commit()
    conn.close()

    return inserted


# =========================
# MARKET DATA
# =========================
def insert_market_data(rows):
    conn = get_conn()
    cursor = conn.cursor()

    inserted = 0

    for m in rows:
        # checagem de duplicação
        cursor.execute("""
            SELECT 1 FROM market_data
            WHERE timestamp = ?
              AND marketId = ?
              AND selectionId = ?
        """, (
            m[1],
            m[2],
            m[4]
        ))

        if cursor.fetchone():
            continue

        cursor.execute("""
            INSERT INTO market_data (
                timestamp,
                marketId,
                tag,
                selectionId,
                selectionName,
                impliedProb,
                bestBid,
                bestAsk,
                spread,
                bidVolume,
                askVolume,
                totalBidVolume,
                totalAskVolume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m[1],   # timestamp
            m[2],   # marketId
            m[3],   # tag
            m[4],   # selectionId
            m[5],   # selectionName
            m[6],   # impliedProb
            m[7],   # bestBid
            m[8],   # bestAsk
            m[9],   # spread
            m[10],  # bidVolume
            m[11],  # askVolume
            m[12],  # totalBidVolume
            m[13],  # totalAskVolume
        ))

        inserted += 1

    conn.commit()
    conn.close()

    return inserted


# =========================
# SYNC
# =========================
def sync():
    data = fetch_data()

    if not data:
        return

    results = data.get("results", [])
    market = data.get("market", [])

    print(f"Recebido: {len(results)} results | {len(market)} market")

    r_inserted = insert_round_results(results)
    m_inserted = insert_market_data(market)

    save_last_sync()

    print(f"Inseridos: {r_inserted} results | {m_inserted} market")
    print("OK\n")


if __name__ == "__main__":
    sync()