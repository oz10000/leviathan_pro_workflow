import requests
import pandas as pd
from signal_engine import compute_features, generate_signal
from timing_engine import estimate_next_signal
from risk_engine import optimal_leverage
import config   # Ahora usamos el módulo config completo

def fetch_top_symbols():
    """Obtiene los TOP_N símbolos según el exchange configurado."""
    if config.EXCHANGE == "binance":
        url = "https://api.binance.com/api/v3/ticker/24hr"
        try:
            data = requests.get(url, timeout=10).json()
            symbols = [s for s in data if s.get("symbol", "").endswith("USDT")]
            sorted_syms = sorted(symbols, key=lambda x: float(x["quoteVolume"]), reverse=True)
            return [s["symbol"] for s in sorted_syms[:config.TOP_N]]
        except Exception:
            return []
    elif config.EXCHANGE == "bybit":
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        try:
            resp = requests.get(url, timeout=10).json()
            items = resp["result"]["list"]
            symbols = [item["symbol"] for item in items if item["symbol"].endswith("USDT")]
            return symbols[:config.TOP_N]
        except Exception:
            return []
    return []

def fetch_latest_candle(symbol):
    """Descarga las últimas velas de 5min para un símbolo."""
    if config.EXCHANGE == "binance":
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit={config.CANDLE_LIMIT}"
        try:
            data = requests.get(url, timeout=10).json()
            df = pd.DataFrame(data, columns=["ts","open","high","low","close","volume","_","_","_","_","_","_"])
            for c in ["open","high","low","close","volume"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["ts"] = pd.to_datetime(df["ts"], unit="ms")
            return compute_features(df)
        except Exception:
            return None
    elif config.EXCHANGE == "bybit":
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=5&limit={config.CANDLE_LIMIT}"
        try:
            resp = requests.get(url, timeout=10).json()
            data = resp["result"]["list"]
            df = pd.DataFrame(data, columns=["ts","open","high","low","close","volume","turnover"])
            df = df.iloc[::-1]  # Orden cronológico
            for c in ["open","high","low","close","volume"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["ts"] = pd.to_datetime(df["ts"].astype(int), unit="ms")
            return compute_features(df)
        except Exception:
            return None
    return None

def scan_top_opportunities():
    """Escanea los top 100 y devuelve las 3 mejores señales."""
    symbols = fetch_top_symbols()
    if not symbols:
        return []
    signals = []
    for sym in symbols:
        df = fetch_latest_candle(sym)
        if df is None or len(df) < 20:
            continue
        sig = generate_signal(df, threshold=config.SCORE_THRESHOLD)
        if sig["signal"] == "WAIT":
            continue
        volatility = df["close"].pct_change().std()
        lev = optimal_leverage(sig["score"], volatility)
        next_min = estimate_next_signal(df)
        signals.append({
            "symbol": sym.replace("USDT","") if config.EXCHANGE=="binance" else sym.replace("USDT",""),
            "signal": sig["signal"],
            "price": sig["price"],
            "score": sig["score"],
            "leverage": lev,
            "next_min": next_min,
            "timestamp": sig["timestamp"]
        })
    signals.sort(key=lambda x: x["score"], reverse=True)
    return signals[:3]
