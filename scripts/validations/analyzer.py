import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import os
from utils.db_client import get_last_n_rows, get_all_tags

def analyze_current_round():
    tags = get_all_tags()
    current_tag = tags[-1][0]
    if not tags:
        print("[AVISO] Nenhum dado disponível.")
        return

    rows = get_last_n_rows(current_tag, 100)
    
    if len(rows) < 2:
        print("[AVISO] Nenhum dado disponível.")
        return
    
    df = pd.DataFrame(rows, columns=[
        "id", "timestamp", "marketId", "tag", "selectionId", "selectionName",
        "impliedProb", "bestBid", "bestAsk", "spread",
        "bidVolume", "askVolume", "totalBidVolume", "totalAskVolume"
    ])
    
    latest_selection = df["selectionName"].iloc[0]
    threshold = latest_selection.split()[-1]
    
    df_current = df[df["selectionName"].str.contains(str(threshold))]
    
    print(f"\n📊 Análise da Rodada Atual (Threshold: {threshold}):")
    print(df_current[["timestamp", "selectionName", "bestBid", "bestAsk", "impliedProb"]])
    
    os.makedirs("data/analysis", exist_ok=True)
    file_path = "data/analysis/current_round.csv"
    df_current.to_csv(file_path, index=False)
    print(f"\n✅ Análise salva em: {file_path}")

def analyze_all_highways():
    """Compara todas as rodovias."""
    tags = get_all_tags()
    
    if len(tags) < 2:
        print("[AVISO] Apenas uma rodovia coletada. Aguarde mais dados.")
        return
    
    print("\n" + "="*80)
    print("🛣️  ANÁLISE DE TODAS AS RODOVIAS")
    print("="*80 + "\n")
    
    for tag in tags:
        rows = get_last_n_rows(tag, n=100)
        
        if not rows:
            continue
        
        df = pd.DataFrame(rows, columns=[
            "id", "timestamp", "marketId", "tag", "selectionId", "selectionName",
            "impliedProb", "bestBid", "bestAsk", "spread",
            "bidVolume", "askVolume", "totalBidVolume", "totalAskVolume"
        ])
        
        print(f"🛣️  {tag}:")
        print(f"   Total de registros: {len(df)}")
        print(f"   Bid médio: {df['bestBid'].mean():.4f}")
        print(f"   Ask médio: {df['bestAsk'].mean():.4f}")
        print(f"   Spread médio: {df['spread'].mean():.4f}")
        print(f"   Prob implícita média: {df['impliedProb'].mean():.2%}")
        print()

if __name__ == "__main__":
    analyze_current_round()
    analyze_all_highways()