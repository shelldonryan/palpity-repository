import os
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from scripts.collector import collect_orderbook
from scripts.collector_result import collect_recent_results
from utils.db_client import init_db, init_results_table

app = Flask(__name__)

# Inicializa banco e scheduler
def initialize_app():
    print("⏳ Inicializando tabelas...")
    init_db()
    init_results_table()
    print("✅ Tabelas prontas")

    # Inicia scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(collect_orderbook, IntervalTrigger(seconds=60), id="collector_job")
    scheduler.add_job(collect_recent_results, IntervalTrigger(seconds=180), id="result_collector_job")
    scheduler.add_job(lambda: print("[INFO] Validação agendada"), IntervalTrigger(hours=1), id="validation_job")
    scheduler.start()
    print("✅ Scheduler iniciado")

    return scheduler

# Inicializa ao começar
scheduler = initialize_app()

# Rotas
@app.route('/')
def health():
    return jsonify({"status": "OK", "scheduler": "running"}), 200

@app.route('/tags')
def tags():
    from utils.db_client import get_all_tags
    data = get_all_tags()
    return jsonify(data)

@app.route('/data')
def data():
    from utils.db_client import get_all_data_results, get_all_data_market
    data_results = get_all_data_results()
    data_market = get_all_data_market()
    return jsonify({"results": data_results, "market": data_market})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)