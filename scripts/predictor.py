# scripts/predictor.py
import pandas as pd
from datetime import datetime

def get_recommendation():
    df = pd.read_csv("data/raw_data.csv")
    if len(df) < 5:
        return "⚠️ Nenhum dado suficiente para previsão. Aguarde mais rodadas."

    now = datetime.now()
    current_hour = now.hour

    # Exemplo: se o preço médio de "Mais de 115" for > 0.60, recomenda comprar
    df["bidPrice"] = pd.to_numeric(df["bidPrice"], errors="coerce")
    more_than_115 = df[df["selectionName"].str.contains("Mais de 115", case=False)]
    up_to_115 = df[df["selectionName"].str.contains("Até 115", case=False)]

    avg_more = more_than_115["bidPrice"].mean()
    avg_up_to = up_to_115["bidPrice"].mean()

    if avg_more > avg_up_to and avg_more > 0.55:
        return f"✅ Recomendação: Comprar 'Mais de 115' (preço médio: {avg_more:.2f})"
    else:
        return f"✅ Recomendação: Comprar 'Até 115' (preço médio: {avg_up_to:.2f})"

if __name__ == "__main__":
    print(get_recommendation())