# utils/db_client.py
import sqlite3
from datetime import datetime

DB_PATH = "data/palpity.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            marketId INTEGER NOT NULL,
            selectionId INTEGER NOT NULL,
            selectionName TEXT NOT NULL,
            impliedProb REAL,
            bestBid REAL NOT NULL,
            bestAsk REAL NOT NULL,
            spread REAL,
            bidVolume REAL,
            askVolume REAL,
            totalBidVolume REAL,
            totalAskVolume REAL
        )
    """)
    conn.commit()
    conn.close()
    print("[INFO] Banco de dados inicializado.")

def save_to_db(data):
    """Salva um registro de coleta no banco."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO market_data (
            timestamp, marketId, selectionId, selectionName,
            impliedProb, bestBid, bestAsk, spread,
            bidVolume, askVolume, totalBidVolume, totalAskVolume
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["marketId"],
        data["selectionId"],
        data["selectionName"],
        data.get("impliedProb", 0.0),
        data["bestBid"],
        data["bestAsk"],
        data.get("spread", 0.0),
        data.get("bidVolume", 0.0),
        data.get("askVolume", 0.0),
        data.get("totalBidVolume", 0.0),
        data.get("totalAskVolume", 0.0)
    ))
    conn.commit()
    conn.close()
    print(f"[INFO] Dados salvos no banco: {data.get('selectionName', 'N/A')} - {data.get('bestBid', 'N/A')}")

def get_last_n_rows(n=10):
    """Retorna os últimos N registros."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM market_data ORDER BY timestamp DESC LIMIT ?
    """, (n,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_hourly_avg():
    """Analisa preço médio e volume por hora e seleção."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            strftime('%H', timestamp) as hour,
            selectionName,
            AVG(bestBid) as avg_bid,
            AVG(bestAsk) as avg_ask,
            AVG(spread) as avg_spread,
            SUM(totalBidVolume) as total_bid_volume,
            SUM(totalAskVolume) as total_ask_volume,
            COUNT(*) as num_rounds
        FROM market_data
        GROUP BY hour, selectionName
        ORDER BY hour, selectionName
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_selection_stats(selection_name):
    """Retorna estatísticas de uma seleção específica."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            selectionName,
            AVG(bestBid) as avg_bid,
            AVG(bestAsk) as avg_ask,
            AVG(spread) as avg_spread,
            AVG(impliedProb) as avg_prob,
            MIN(bestBid) as min_bid,
            MAX(bestAsk) as max_ask,
            COUNT(*) as total_rounds
        FROM market_data
        WHERE selectionName = ?
        GROUP BY selectionName
    """, (selection_name,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_trend(selection_name, hours=1):
    """Retorna a tendência de preço nas últimas N horas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            timestamp,
            bestBid,
            bestAsk,
            spread,
            impliedProb
        FROM market_data
        WHERE selectionName = ?
        AND timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp DESC
    """, (selection_name, hours))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_best_prices():
    """Retorna o melhor bid/ask atual para cada seleção."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT
            selectionName,
            (SELECT bestBid FROM market_data m2 
             WHERE m2.selectionName = m1.selectionName 
             ORDER BY m2.timestamp DESC LIMIT 1) as current_bid,
            (SELECT bestAsk FROM market_data m2 
             WHERE m2.selectionName = m1.selectionName 
             ORDER BY m2.timestamp DESC LIMIT 1) as current_ask,
            (SELECT impliedProb FROM market_data m2 
             WHERE m2.selectionName = m1.selectionName 
             ORDER BY m2.timestamp DESC LIMIT 1) as current_prob
        FROM market_data m1
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def export_to_csv(filename="data/export.csv"):
    """Exporta todos os dados para CSV."""
    import pandas as pd
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM market_data", conn)
    conn.close()
    df.to_csv(filename, index=False)
    print(f"[INFO] Dados exportados para {filename}")