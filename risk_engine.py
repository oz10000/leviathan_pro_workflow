def optimal_leverage(score, volatility):
    """Apalancamiento dinámico entre 5x y 8x basado en score y volatilidad."""
    if score >= 85:
        lev = 8
    elif score >= 75:
        lev = 6 + (score - 75) / 10 * 2  # escala lineal de 6 a 8
    else:
        lev = 5
    vol_penalty = volatility * 10
    return max(5, min(8, lev - vol_penalty))
