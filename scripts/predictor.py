import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datetime import datetime
from utils.db_client import (get_last_n_rows, get_all_tags, get_results_by_threshold)

def get_historical_accuracy(tag, threshold):
    """Calcula a acurácia histórica para um threshold específico."""
    results = get_results_by_threshold(tag, threshold, limit=50)
    
    if not results:
        return None
    
    df = pd.DataFrame(results, columns=[
        "id", "marketId", "tag", "threshold", "resultSelectionId",
        "resultSelectionName", "impliedProbWinner", "impliedProbLoser",
        "resolvedAt", "createdAt"
    ])
    
    mais_de_wins = len(df[df["resultSelectionName"].str.contains("Mais de")])
    ate_wins = len(df[df["resultSelectionName"].str.contains("Até")])
    total = len(df)
    
    return {
        "mais_de_win_rate": mais_de_wins / total if total > 0 else 0.5,
        "ate_win_rate": ate_wins / total if total > 0 else 0.5,
        "total_rounds": total
    }

def get_recommendation_with_history(tag):
    """Gera recomendação considerando histórico de resultados."""
    rows = get_last_n_rows(tag, n=100)
    
    if len(rows) < 10:
        return f"⚠️ Dados insuficientes para {tag}."
    
    df = pd.DataFrame(rows, columns=[
        "id", "timestamp", "marketId", "tag", "selectionId", "selectionName",
        "impliedProb", "bestBid", "bestAsk", "spread",
        "bidVolume", "askVolume", "totalBidVolume", "totalAskVolume"
    ])
    
    threshold = df["selectionName"].iloc[0].split()[-1]
    
    print(f"\n{'='*80}")
    print(f"🛣️  {tag} | Threshold: {threshold}")
    print(f"{'='*80}\n")
    
    # Dados atuais do orderbook
    mais_de = df[(df["selectionName"].str.contains("Mais de")) & 
                 (df["bestBid"] > 0) & (df["bestAsk"] > 0)]
    ate = df[(df["selectionName"].str.contains("Até")) & 
             (df["bestBid"] > 0) & (df["bestAsk"] > 0)]
    
    if mais_de.empty or ate.empty:
        return f"⚠️ Dados incompletos para {tag}."
    
    mais_de_prob = mais_de["impliedProb"].mean()
    ate_prob = ate["impliedProb"].mean()
    mais_de_bid = mais_de["bestBid"].mean()
    ate_bid = ate["bestBid"].mean()
    
    # Histórico de resultados
    history = get_historical_accuracy(tag, int(threshold))
    
    print(f"📊 Dados Atuais:")
    print(f"   Mais de {threshold}: Prob={mais_de_prob:.2%}, Bid={mais_de_bid:.4f}")
    print(f"   Até {threshold}: Prob={ate_prob:.2%}, Bid={ate_bid:.4f}")
    
    if history:
        print(f"\n📈 Histórico (últimas {history['total_rounds']} rodadas):")
        print(f"   'Mais de' venceu: {history['mais_de_win_rate']:.1%}")
        print(f"   'Até' venceu: {history['ate_win_rate']:.1%}")
    
    # Lógica melhorada: combina dados atuais + histórico
    if history:
        # Peso: 60% dados atuais, 40% histórico
        mais_de_score = (mais_de_prob * 0.6) + (history['mais_de_win_rate'] * 0.4)
        ate_score = (ate_prob * 0.6) + (history['ate_win_rate'] * 0.4)
    else:
        mais_de_score = mais_de_prob
        ate_score = ate_prob
    
    print(f"\n🎯 Score Ponderado (60% atual + 40% histórico):")
    print(f"   Mais de {threshold}: {mais_de_score:.2%}")
    print(f"   Até {threshold}: {ate_score:.2%}")
    
    # Recomendação
    if mais_de_score > ate_score and mais_de_score > 0.55:
        return f"\n✅ Recomendação: Comprar 'Mais de {threshold}' (Score: {mais_de_score:.1%})"
    elif ate_score > mais_de_score and ate_score > 0.55:
        return f"\n✅ Recomendação: Comprar 'Até {threshold}' (Score: {ate_score:.1%})"
    else:
        return f"\n⚖️ Mercado equilibrado — sem recomendação clara."

def main():
    tags = get_all_tags()
    
    if not tags:
        print("⚠️ Nenhum dado disponível.")
        return
    
    print(f"\n🤖 PREVISÕES COM HISTÓRICO DE RESULTADOS")
    print(f"⏱️ {datetime.now().strftime('%H:%M:%S')}\n")
    
    for tag in tags:
        recommendation = get_recommendation_with_history(tag[0])
        print(recommendation)
        print()

if __name__ == "__main__":
    main()