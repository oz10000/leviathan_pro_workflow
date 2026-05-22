import numpy as np

def estimate_next_signal(df):
    if len(df) < 20:
        return 60
    volatility = float(df["close"].pct_change().std())
    trend_strength = float(abs(df["ema20"].iloc[-1] - df["ema50"].iloc[-1]))
    base_cycle = 60
    adjustment = (volatility * 500.0) + (1.0 / (trend_strength + 0.0001))
    next_signal_minutes = max(5, int(base_cycle - adjustment))
    return next_signal_minutes

def estimate_signal_duration(df):
    """Duración probable de la señal actual en minutos (máximo 15)."""
    atr_pct = df["atr"].iloc[-1] / df["close"].iloc[-1]
    volume_ratio = df["volume_ratio"].iloc[-1]
    slope = abs(df["slope_ema20"].iloc[-1])
    duration = 5 + int((atr_pct * 1000) + (volume_ratio * 2) + (slope * 500))
    return min(duration, 15)
