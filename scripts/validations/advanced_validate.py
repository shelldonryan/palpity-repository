import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# scripts/validate_advanced.py
import pandas as pd
from datetime import datetime
from utils.db_client import get_results_with_datetime_analysis, get_all_tags, init_results_table

def analyze_by_hour_and_day(tag=None):
    """Analisa acurácia por hora e dia da semana."""
    init_results_table()
    
    results = get_results_with_datetime_analysis(tag)
    
    if not results:
        print("⚠️ Nenhum resultado disponível.")
        return
    
    df = pd.DataFrame(results, columns=[
        "marketId", "tag", "threshold", "resultSelectionName", "impliedProbWinner",
        "resolvedAt", "hour", "day_of_week", "day_name"
    ])
    
    # Converte tipos
    df["hour"] = df["hour"].astype(int)
    df["impliedProbWinner"] = pd.to_numeric(df["impliedProbWinner"])
    
    print("\n" + "="*100)
    print("📊 ANÁLISE AVANÇADA DE ACURÁCIA")
    print("="*100)
    
    if tag:
        print(f"\n🛣️  Rodovia: {tag}\n")
    else:
        print(f"\n🌍 Todas as rodovias\n")
    
    # ===== ANÁLISE POR HORA =====
    print("\n" + "-"*100)
    print("⏰ ANÁLISE POR HORA DO DIA")
    print("-"*100 + "\n")
    
    hourly_analysis = df.groupby("hour").agg({
        "resultSelectionName": "count",
        "impliedProbWinner": "mean"
    }).rename(columns={
        "resultSelectionName": "total_rodadas",
        "impliedProbWinner": "prob_media_vencedor"
    })
    
    # Calcula taxa de "Mais de"
    for hour in hourly_analysis.index:
        hour_data = df[df["hour"] == hour]
        mais_de = len(hour_data[hour_data["resultSelectionName"].str.contains("Mais de")])
        ate = len(hour_data[hour_data["resultSelectionName"].str.contains("Até")])
        total = len(hour_data)
        
        mais_de_pct = (mais_de / total * 100) if total > 0 else 0
        
        print(f"  {hour:02d}:00 - {hour:02d}:59")
        print(f"    Total: {total} rodadas | Mais de: {mais_de_pct:.1f}% | Até: {100-mais_de_pct:.1f}%")
        print(f"    Prob média do vencedor: {hourly_analysis.loc[hour, 'prob_media_vencedor']:.2%}")
        print()
    
    # ===== ANÁLISE POR DIA DA SEMANA =====
    print("\n" + "-"*100)
    print("📅 ANÁLISE POR DIA DA SEMANA")
    print("-"*100 + "\n")
    
    daily_analysis = df.groupby(["day_of_week", "day_name"]).agg({
        "resultSelectionName": "count",
        "impliedProbWinner": "mean"
    }).rename(columns={
        "resultSelectionName": "total_rodadas",
        "impliedProbWinner": "prob_media_vencedor"
    })
    
    for (day_num, day_name), row in daily_analysis.iterrows():
        day_data = df[df["day_name"] == day_name]
        mais_de = len(day_data[day_data["resultSelectionName"].str.contains("Mais de")])
        ate = len(day_data[day_data["resultSelectionName"].str.contains("Até")])
        total = len(day_data)
        
        mais_de_pct = (mais_de / total * 100) if total > 0 else 0
        
        print(f"  {day_name}")
        print(f"    Total: {total} rodadas | Mais de: {mais_de_pct:.1f}% | Até: {100-mais_de_pct:.1f}%")
        print(f"    Prob média do vencedor: {row['prob_media_vencedor']:.2%}")
        print()
    
    # ===== ANÁLISE CRUZADA (HORA + DIA) =====
    print("\n" + "-"*100)
    print("🔄 ANÁLISE CRUZADA (HORA + DIA DA SEMANA)")
    print("-"*100 + "\n")
    
    crosstab = df.groupby(["hour", "day_name"]).size().unstack(fill_value=0)
    
    print("Distribuição de rodadas por hora e dia:\n")
    print(crosstab.to_string())
    
    # ===== PADRÕES IDENTIFICADOS =====
    print("\n" + "-"*100)
    print("🎯 PADRÕES IDENTIFICADOS")
    print("-"*100 + "\n")
    
    # Hora com mais "Mais de"
    hourly_mais_de = {}
    for hour in df["hour"].unique():
        hour_data = df[df["hour"] == hour]
        mais_de_pct = len(hour_data[hour_data["resultSelectionName"].str.contains("Mais de")]) / len(hour_data) * 100
        hourly_mais_de[hour] = mais_de_pct
    
    best_hour = max(hourly_mais_de, key=hourly_mais_de.get)
    print(f"  ✅ Melhor hora para 'Mais de': {best_hour:02d}:00 ({hourly_mais_de[best_hour]:.1f}%)")
    
    # Dia com mais "Mais de"
    daily_mais_de = {}
    for day in df["day_name"].unique():
        day_data = df[df["day_name"] == day]
        mais_de_pct = len(day_data[day_data["resultSelectionName"].str.contains("Mais de")]) / len(day_data) * 100
        daily_mais_de[day] = mais_de_pct
    
    best_day = max(daily_mais_de, key=daily_mais_de.get)
    print(f"  ✅ Melhor dia para 'Mais de': {best_day} ({daily_mais_de[best_day]:.1f}%)")
    
    # Melhor combinação hora + dia
    df_crosstab = df.copy()
    df_crosstab["mais_de"] = df_crosstab["resultSelectionName"].str.contains("Mais de")
    best_combo = df_crosstab.groupby(["hour", "day_name"])["mais_de"].agg(["sum", "count"])
    best_combo["pct"] = (best_combo["sum"] / best_combo["count"] * 100)
    best_combo = best_combo[best_combo["count"] >= 2]  # Apenas combos com 2+ rodadas
    
    if not best_combo.empty:
        best_row = best_combo.sort_values("pct", ascending=False).iloc[0]
        hour, day = best_row.name
        print(f"  ✅ Melhor combinação: {day} às {hour:02d}:00 ({best_row['pct']:.1f}%)")
        
    print("\n" + "="*100 + "\n")

def analyze_all_rodovias():
    """Analisa cada rodovia separadamente."""
    tags = get_all_tags()
    
    if not tags:
        print("⚠️ Nenhum dado disponível.")
        return
    
    for tag in tags:
        analyze_by_hour_and_day(tag[0])

if __name__ == "__main__":
    print("\n🔍 VALIDAÇÃO AVANÇADA\n")
    
    tags = get_all_tags()
    
    if not tags:
        print("⚠️ Nenhum dado disponível.")
    else:
        # Analisa todas as rodovias
        for tag in tags:
            analyze_by_hour_and_day(tag[0])