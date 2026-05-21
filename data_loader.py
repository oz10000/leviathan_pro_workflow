import pandas as pd
from signal_engine import compute_features

def load_cached_data(symbol="BTC", timeframe="5m", limit=500):
    """
    Carga datos históricos desde un archivo CSV pre‑descargado.
    En un sistema real, aquí iría la conexión a la API del exchange.
    """
    try:
        df = pd.read_csv(f"data/{symbol}_{timeframe}.csv")
        df["ts"] = pd.to_datetime(df["ts"])
        df = compute_features(df)
        return df
    except FileNotFoundError:
        # Datos de ejemplo para pruebas
        dates = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq="5min")
        df = pd.DataFrame({
            "ts": dates,
            "open": 100.0, "high": 102.0, "low": 98.0, "close": 100.0, "volume": 1000.0
        })
        return compute_features(df)
