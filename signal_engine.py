import pandas as pd
import numpy as np


def compute_features(df):
    """Calcula todos los indicadores técnicos y el score compuesto."""
    df = df.copy()

    # ---- ATR ----
    df["prev_close"] = df["close"].shift(1)
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["prev_close"]),
            abs(df["low"] - df["prev_close"]),
        ),
    )
    df["atr"] = df["tr"].rolling(14).mean()
    df["atr_pct"] = df["atr"] / df["close"]

    # ---- EMAs ----
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["slope_ema20"] = df["ema20"].diff(5) / df["ema20"].shift(5)

    # ---- Volumen ----
    df["volume_avg"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["volume_avg"]

    # ---- RSI (14) ----
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df["rsi"] = 100.0 - (100.0 / (1.0 + rs))

    # ---- MACD ----
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # ---- Score compuesto (0–100) ----
    trend_score = 100.0 if df["ema20"].iloc[-1] > df["ema50"].iloc[-1] else 30.0
    rsi_score = 100.0 - abs(df["rsi"].fillna(50) - 50.0)  # 50 → 100, extremos → menos
    volume_score = df["volume_ratio"].clip(0.5, 2.0).fillna(1.0) * 50.0
    slope_score = (
        df["slope_ema20"]
        .fillna(0)
        .apply(lambda x: min(max(x * 1000.0, 0.0), 100.0))
    )

    df["score"] = (
        0.30 * trend_score
        + 0.25 * rsi_score
        + 0.25 * volume_score
        + 0.20 * slope_score
    )

    return df


def generate_signal(df, threshold=68):
    """Retorna la señal actual basada en el último candle."""
    if len(df) < 20:
        return None

    last = df.iloc[-1]
    score = float(last["score"])

    direction = None
    if score >= threshold:
        direction = "BUY" if last["ema20"] > last["ema50"] else "SELL"

    return {
        "signal": direction if direction else "WAIT",
        "score": score,
        "price": float(last["close"]),
        "timestamp": (
            str(last["ts"])
            if "ts" in last and pd.notna(last["ts"])
            else str(pd.Timestamp.now())
        ),
        "atr": (
            float(last["atr"])
            if "atr" in last and pd.notna(last["atr"])
            else float(last["close"]) * 0.005
        ),
    }
