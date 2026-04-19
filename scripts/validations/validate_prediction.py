import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from utils.db_client import get_results_by_tag, init_results_table

def analyze_accuracy_by_tag(tag):
    """Analisa acurácia das previsões por rodovia."""
    results = get_results_by_tag(tag, limit=100)
    
    if len(results) < 5:
        return None
    
    results_df = pd.DataFrame(results, columns=[
        "id", "marketId", "tag", "threshold", "resultSelectionId",
        "resultSelectionName", "impliedProbWinner", "impliedProbLoser",
        "resolvedAt", "createdAt"
    ])
    
    print(f"\n{'='*80}")
    print(f"🛣️  ANÁLISE DE ACURÁCIA: {tag}")
    print(f"{'='*80}\n")
    
    # Estatísticas gerais
    total_rounds = len(results_df)
    mais_de_wins = len(results_df[results_df["resultSelectionName"].str.contains("Mais de")])
    ate_wins = len(results_df[results_df["resultSelectionName"].str.contains("Até")])
    
    print(f"📊 Estatísticas Gerais:")
    print(f"   Total de rodadas: {total_rounds}")
    print(f"   'Mais de' venceu: {mais_de_wins} vezes ({mais_de_wins/total_rounds*100:.1f}%)")
    print(f"   'Até' venceu: {ate_wins} vezes ({ate_wins/total_rounds*100:.1f}%)")
    
    # Por threshold
    print(f"\n🎯 Resultados por Threshold:")
    for threshold in sorted(results_df["threshold"].unique()):
        df_threshold = results_df[results_df["threshold"] == threshold]
        mais_de = len(df_threshold[df_threshold["resultSelectionName"].str.contains("Mais de")])
        ate = len(df_threshold[df_threshold["resultSelectionName"].str.contains("Até")])
        print(f"   Threshold {threshold}: Mais de={mais_de}, Até={ate}")
    
    # Calibração de probabilidades
    print(f"\n📈 Calibração de Probabilidades:")
    results_df["impliedProbWinner"] = pd.to_numeric(results_df["impliedProbWinner"])
    
    avg_prob = results_df["impliedProbWinner"].mean()
    print(f"   Probabilidade média do vencedor: {avg_prob:.2%}")
    
    # Agrupa por faixas de probabilidade
    results_df["prob_bucket"] = pd.cut(results_df["impliedProbWinner"], 
                                        bins=[0, 0.3, 0.5, 0.7, 1.0],
                                        labels=["0-30%", "30-50%", "50-70%", "70-100%"])
    
    print(f"\n   Distribuição de probabilidades:")
    for bucket in ["0-30%", "30-50%", "50-70%", "70-100%"]:
        count = len(results_df[results_df["prob_bucket"] == bucket])
        if count > 0:
            pct = count / total_rounds * 100
            print(f"      {bucket}: {count} resultados ({pct:.1f}%)")
    
    # Últimos resultados
    print(f"\n📋 Últimos 10 Resultados:")
    print(results_df[["threshold", "resultSelectionName", "impliedProbWinner", "resolvedAt"]].head(10).to_string(index=False))
    
    print(f"\n{'='*80}\n")
    
    return {
        "tag": tag,
        "total_rounds": total_rounds,
        "mais_de_wins": mais_de_wins,
        "ate_wins": ate_wins,
        "avg_prob": avg_prob
    }

def analyze_all_tags():
    """Analisa acurácia para todas as rodovias."""
    from utils.db_client import get_all_tags
    
    tags = get_all_tags()
    
    if not tags:
        print("⚠️ Nenhum dado disponível.")
        return
    
    print("\n🤖 ANÁLISE DE ACURÁCIA - TODAS AS RODOVIAS\n")
    
    summary = []
    for tag in tags:
        result = analyze_accuracy_by_tag(tag[0])
        if result:
            summary.append(result)
    
    # Resumo comparativo
    if summary:
        print("\n" + "="*80)
        print("📊 RESUMO COMPARATIVO")
        print("="*80 + "\n")
        
        for item in summary:
            print(f"🛣️  {item['tag']}:")
            print(f"   Total: {item['total_rounds']} | Mais de: {item['mais_de_wins']} | Até: {item['ate_wins']}")
            print(f"   Prob média: {item['avg_prob']:.2%}\n")

if __name__ == "__main__":
    init_results_table()
    analyze_all_tags()