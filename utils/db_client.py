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
            tag TEXT NOT NULL,
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

def init_results_table():
    """Cria tabela para armazenar resultados das rodadas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS round_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marketId INTEGER NOT NULL UNIQUE,
            tag TEXT NOT NULL,                          
            threshold INTEGER NOT NULL,
            resultSelectionId INTEGER NOT NULL,
            resultSelectionName TEXT NOT NULL,          
            impliedProbWinner REAL,                     
            impliedProbLoser REAL,                      
            resolvedAt TEXT NOT NULL,
            createdAt TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(data):
    """Salva um registro de coleta no banco."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO market_data (
            timestamp, marketId, tag, selectionId, selectionName,
            impliedProb, bestBid, bestAsk, spread,
            bidVolume, askVolume, totalBidVolume, totalAskVolume
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["marketId"],
        data["tag"],
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

def save_result(data):
    """Salva o resultado de uma rodada."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO round_results (
                marketId, tag, threshold, resultSelectionId, resultSelectionName,
                impliedProbWinner, impliedProbLoser, resolvedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data["marketId"], data["tag"], data["threshold"], data["resultSelectionId"], data["resultName"], data["probWinner"], data["probLoser"], data["resolvedAt"]))
        conn.commit()
        print(f"[INFO] Resultado salvo: {data['resultName']} venceu (Market {data['marketId']})")
    except sqlite3.IntegrityError:
        print(f"[AVISO] Resultado para Market {data['marketId']} já existe no banco.")
    finally:
        conn.close()

def get_last_n_rows(tag, n=10):
    """Retorna os últimos N registros."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM market_data WHERE tag = ? ORDER BY timestamp DESC LIMIT ?
    """, (tag, n))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_tags():
    """Retorna todas as tags (rodovias) coletadas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT tag FROM market_data ORDER BY tag
    """)
    rows = cursor.fetchall()
    conn.close()
    return [row for row in rows]

def get_hourly_avg(tag):
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
        WHERE tag = ?
        GROUP BY hour, selectionName
        ORDER BY hour, selectionName
    """, (tag))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_selection_stats(tag, selection_name):
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
        WHERE tag = ? AND selectionName = ?
        GROUP BY selectionName
    """, (tag, selection_name))
    row = cursor.fetchone()
    conn.close()
    return row

def get_trend(tag, selection_name, hours=1):
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
        WHERE tag = ? AND selectionName = ?
        AND timestamp > datetime('now', '-' || ? || ' hours')
        ORDER BY timestamp DESC
    """, (tag, selection_name, hours))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_best_prices(tag):
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
        WHERE tag = ?
    """, (tag))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_result_by_market_id(tag, market_id):
    """Busca o resultado de um mercado específico."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM round_results WHERE tag = ? AND marketId = ?
    """, (tag, market_id))
    row = cursor.fetchone()
    conn.close()
    return row

def get_results_by_tag(tag, limit=100):
    """Retorna resultados de uma rodovia específica."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM round_results 
        WHERE tag = ?
        ORDER BY resolvedAt DESC 
        LIMIT ?
    """, (tag, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_results_with_datetime_analysis(tag=None):
    """Retorna resultados com análise de hora e dia da semana."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT 
            marketId,
            tag,
            threshold,
            resultSelectionName,
            impliedProbWinner,
            resolvedAt,
            strftime('%H', resolvedAt) as hour,
            strftime('%w', resolvedAt) as day_of_week,
            CASE 
                WHEN strftime('%w', resolvedAt) = '0' THEN 'Domingo'
                WHEN strftime('%w', resolvedAt) = '1' THEN 'Segunda'
                WHEN strftime('%w', resolvedAt) = '2' THEN 'Terça'
                WHEN strftime('%w', resolvedAt) = '3' THEN 'Quarta'
                WHEN strftime('%w', resolvedAt) = '4' THEN 'Quinta'
                WHEN strftime('%w', resolvedAt) = '5' THEN 'Sexta'
                WHEN strftime('%w', resolvedAt) = '6' THEN 'Sábado'
            END as day_name
        FROM round_results
    """
    
    if tag:
        query += f" WHERE tag = '{tag}'"
    
    query += " ORDER BY resolvedAt DESC"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_results_by_threshold(tag, threshold, limit=50):
    """Retorna resultados de um threshold específico em uma rodovia."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM round_results 
        WHERE tag = ? AND threshold = ?
        ORDER BY resolvedAt DESC 
        LIMIT ?
    """, (tag, threshold, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_data_results(since):
    """Retorna todos os dados do banco."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM round_results WHERE resolvedAt > ?", [since])
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_data_market(since):
    """Retorna todos os dados do banco."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM market_data WHERE timestamp > ?", [since])
    rows = cursor.fetchall()
    conn.close()
    return rows

def compare_prediction_vs_result(predicted_selection, actual_result_name):
    """Compara previsão com resultado real."""
    return predicted_selection.lower() == actual_result_name.lower()