import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from scripts.collector import collect_orderbook
from scripts.collector_result import collect_recent_results
from utils.db_client import init_db, init_results_table
scheduler = BackgroundScheduler()

def initialize_databases():    
    try:
        print("  ⏳ Inicializando tabela de market_data...", end=" ", flush=True)
        init_db()
        print("✅ OK\n")
    except Exception as e:
        print(f"❌ ERRO: {e}\n")
        return False
    
    try:
        print("  ⏳ Inicializando tabela de resultados...", end=" ", flush=True)
        init_results_table()
        print("✅ OK\n")
    except Exception as e:
        print(f"❌ ERRO: {e}\n")
        return False
    
    return True

init = initialize_databases()

if init:
    scheduler.add_job(
        collect_orderbook,
        IntervalTrigger(seconds=60),
        id="collector_job",
        name="Collector",
        replace_existing=True
    )

    scheduler.add_job(
        collect_recent_results,
        IntervalTrigger(seconds=180),
        id="result_collector_job",
        name="Result Collector",
        replace_existing=True
    )

    scheduler.add_job(
        lambda: print("[INFO] Validação agendada"),
        IntervalTrigger(hours=1),
        id="validation_job",
        name="Validation",
        replace_existing=True
    )

    scheduler.start()

    print("[INFO] Scheduler iniciado")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        scheduler.shutdown()