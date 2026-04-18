import pandas as pd
from datetime import datetime

def analyze_data():
    df = pd.read_csv("data/raw_data.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    # Analisa preço médio por seleção
    avg_price = df.groupby("selectionName")["bidPrice"].mean().reset_index()
    print("📊 Preço médio por seleção:")
    print(avg_price)

    # Analisa volume por hora
    hourly_volume = df.groupby("hour")["bidQuantity"].sum().reset_index()
    print("🕒 Volume por hora:")
    print(hourly_volume)

    # Salva análise
    avg_price.to_csv("data/selection_avg_price.csv", index=False)
    hourly_volume.to_csv("data/hourly_volume.csv", index=False)

if __name__ == "__main__":
    analyze_data()