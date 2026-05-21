import requests
import pandas as pd
from signal_engine import compute_features, generate_signal
from timing_engine import estimate_next_signal
from risk_engine import optimal_leverage
from config import EXCHANGE, TOP_N

def fetch_top_symbols():
    if EXCHANGE == "binance":
        url = "https://api.binance.com/api/v3/ticker/24hr"
        data = requests.get(url, timeout=10).json()
        symbols = [s for s in data if s["symbol"].endswith("USDT")]
        sorted_syms = sorted(symbols, key=lambda x: float(x["quoteVolume"]), reverse=True)
        return [s["symbol"] for s in sorted_syms[:TOP_N]]
    elif EXCHANGE == "bybit":
        url = "https://api.bybit.com/v5/market/tickers?category=linear"
        resp = requests.get(url, timeout=10).json()
        symbols = [item["symbol"] for item in resp["result"]["list"] if item["symbol"].endswith("USDT")]
        return symbols[:TOP_N]  # Bybit ordena aprox. por volumen
    return []

def fetch_latest_candle(symbol):
    if EXCHANGE == "binance":
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=50"
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=["ts","open","high","low","close","volume","_","_","_","_","_","_"])
        for c in ["open","high","low","close","volume"]:
            df[c] = pd.to_numeric(df[c])
        df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    elif EXCHANGE == "bybit":
        url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=5&limit=50"
        resp = requests.get(url).json()
        data = resp["result"]["list"]
        df = pd.DataFrame(data, columns=["ts","open","high","low","close","volume","turnover"])
        df = df.iloc[::-1]  # Orden cronológico
        for c in ["open","high","low","close","volume"]:
            df[c] = pd.to_numeric(df[c])
        df["ts"] = pd.to_datetime(df["ts"].astype(int), unit="ms")
    else:
        return None
    return compute_features(df)

def scan_top_opportunities():
    symbols = fetch_top_symbols()
    signals = []
    for sym in symbols:
        df = fetch_latest_candle(sym)
        if df is None or len(df) < 20:
            continue
        sig = generate_signal(df)
        if sig["signal"] == "WAIT":
            continue
        volatility = df["close"].pct_change().std()
        lev = optimal_leverage(sig["score"], volatility)
        next_min = estimate_next_signal(df)
        signals.append({
            "symbol": sym.replace("USDT","") if EXCHANGE=="binance" else sym.replace("USDT",""),
            "signal": sig["signal"],
            "price": sig["price"],
            "score": sig["score"],
            "leverage": lev,
            "next_min": next_min,
            "timestamp": sig["timestamp"]
        })
    signals.sort(key=lambda x: x["score"], reverse=True)
    return signals[:3]
