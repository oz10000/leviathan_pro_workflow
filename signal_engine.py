import pandas as pd
import numpy as np

def compute_features(df):
    df = df.copy()
    df["tr"] = np.maximum(df["high"] - df["low"],
                          np.maximum(abs(df["high"] - df["close"].shift(1)),
                                     abs(df["low"] - df["close"].shift(1))))
    df["atr"] = df["tr"].rolling(14).mean()
    df["atr_pct"] = df["atr"] / df["close"]
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["slope_ema20"] = df["ema20"].diff(5) / df["ema20"].shift(5)
    df["volume_avg"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_avg"]
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df["rsi"] = 100.0 - (100.0 / (1.0 + rs))
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    # Score compuesto original
    trend_score = 100 if df["ema20"].iloc[-1] > df["ema50"].iloc[-1] else 30
    df["score"] = (0.30 * trend_score +
                   0.25 * (100 - abs(df["rsi"] - 50)) +
                   0.25 * df["volume_ratio"].clip(0.5, 2) * 50 +
                   0.20 * df["slope_ema20"].fillna(0).apply(lambda x: min(max(x * 1000, 0), 100)))
    return df

def generate_signal(df, threshold=68):
    """Retorna la señal actual basada en el último candle."""
    if len(df) < 20:
        return None
    last = df.iloc[-1]
    score = last["score"]
    direction = None
    if score >= threshold:
        direction = "BUY" if last["ema20"] > last["ema50"] else "SELL"
    return {
        "signal": direction if direction else "WAIT",
        "score": float(score),
        "price": float(last["close"]),
        "timestamp": str(last["ts"]) if "ts" in last else str(pd.Timestamp.now()),
        "atr": float(last["atr"]) if not pd.isna(last["atr"]) else float(last["close"]) * 0.005
    }
