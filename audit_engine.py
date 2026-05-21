def audit_last_signal(last_signal, df_future):
    """
    Evalúa el resultado de la última señal usando datos posteriores.
    df_future: DataFrame con velas posteriores a la señal (debe contener 'close').
    """
    if not last_signal or last_signal["signal"] == "WAIT":
        return None
    entry = last_signal["price"]
    direction = last_signal["signal"]
    if df_future.empty:
        return {"status": "pending"}

    future_prices = df_future["close"].values
    best_move = (future_prices.max() - entry) / entry
    worst_move = (future_prices.min() - entry) / entry

    if direction == "BUY":
        pnl_pct = best_move
    else:
        pnl_pct = -worst_move

    return {
        "pnl_pct": round(pnl_pct * 100, 2),
        "result": "WIN" if pnl_pct > 0 else "LOSS",
        "max_favorable": round(best_move * 100, 2),
        "max_adverse": round(worst_move * 100, 2)
    }
