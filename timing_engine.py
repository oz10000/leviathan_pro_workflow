import numpy as np


def estimate_next_signal(df):
    """
    Estima los minutos hasta la próxima señal basada en volatilidad y fuerza de tendencia.
    """
    if len(df) < 20:
        return 60

    volatility = float(df["close"].pct_change().std())
    trend_strength = float(abs(df["ema20"].iloc[-1] - df["ema50"].iloc[-1]))

    base_cycle = 60  # minutos base entre señales
    adjustment = (volatility * 500.0) + (1.0 / (trend_strength + 0.0001))

    next_signal_minutes = max(5, int(base_cycle - adjustment))
    return next_signal_minutes
