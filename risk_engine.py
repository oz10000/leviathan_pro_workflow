def optimal_leverage(score, volatility):
    """
    Apalancamiento dinámico entre 5x y 8x basado en score y volatilidad.
    """
    if score >= 85:
        lev = 8.0
    elif score >= 75:
        lev = 6.0 + (score - 75.0) / 10.0 * 2.0  # escala lineal de 6 a 8
    else:
        lev = 5.0

    vol_penalty = volatility * 10.0
    return max(5.0, min(8.0, lev - vol_penalty))
