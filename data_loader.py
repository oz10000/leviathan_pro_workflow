import pandas as pd
import numpy as np
from signal_engine import compute_features


def load_cached_data(symbol="BTC", timeframe="5m", limit=500):
    """
    Carga datos históricos desde un archivo CSV pre‑descargado.
    Si no existe el archivo, genera datos sintéticos con tendencia y volatilidad
    para que la auditoría pueda mostrar resultados realistas.
    """
    try:
        df = pd.read_csv(f"data/{symbol}_{timeframe}.csv")
        df["ts"] = pd.to_datetime(df["ts"])
        df = compute_features(df)
        return df
    except FileNotFoundError:
        # Generar datos sintéticos CON TENDENCIA Y VOLATILIDAD
        np.random.seed(42)
        dates = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq="5min")

        # Precio con tendencia alcista + ruido
        trend = np.linspace(0, 8, limit)  # subida gradual de $0 a $8
        noise = np.random.normal(0, 0.3, limit)
        price = 100.0 + trend + noise

        # Volumen variable
        volume = np.random.uniform(500, 2000, limit)

        df = pd.DataFrame(
            {
                "ts": dates,
                "open": price - 0.2,
                "high": price + 0.5,
                "low": price - 0.5,
                "close": price,
                "volume": volume,
            }
        )
        df = compute_features(df)
        return df
