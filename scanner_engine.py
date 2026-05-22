import requests
import pandas as pd
import time
from signal_engine import compute_features, generate_signal
from timing_engine import estimate_next_signal
from risk_engine import optimal_leverage
import config

# Cabecera necesaria para evitar bloqueos por falta de User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _get_base_url():
    """Devuelve la URL base sin restricción geográfica para el exchange actual."""
    return config.ENDPOINTS[config.EXCHANGE]["base_url"]


def fetch_top_symbols():
    """
    Obtiene los TOP_N símbolos por volumen de 24h.
    Usa el endpoint sin restricción geográfica.
    """
    ep = config.ENDPOINTS[config.EXCHANGE]
    url = _get_base_url() + ep["ticker_path"]

    try:
        if config.EXCHANGE == "binance":
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            symbols = [s for s in data if isinstance(s, dict) and s.get("symbol", "").endswith("USDT")]
            sorted_syms = sorted(symbols, key=lambda x: float(x.get("quoteVolume", 0)), reverse=True)
            return [s["symbol"] for s in sorted_syms[: config.TOP_N]]

        elif config.EXCHANGE == "bybit":
            params = {"category": "linear"}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("result", {}).get("list", [])
            symbols = [item for item in items if item.get("symbol", "").endswith("USDT")]
            sorted_syms = sorted(symbols, key=lambda x: float(x.get("turnover24h", 0)), reverse=True)
            return [s["symbol"] for s in sorted_syms[: config.TOP_N]]

    except Exception as e:
        return {"error": str(e)}

    return {"error": "Exchange no soportado"}


def fetch_latest_candle(symbol):
    """Descarga las últimas velas de 5min usando el endpoint sin restricción."""
    ep = config.ENDPOINTS[config.EXCHANGE]

    if config.EXCHANGE == "binance":
        url = f"{_get_base_url()}{ep['klines_path']}?symbol={symbol}&interval=5m&limit={config.CANDLE_LIMIT}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if not data or not isinstance(data, list):
                return None
            df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume",
                                             "_", "_", "_", "_", "_", "_"])
            for c in ["open", "high", "low", "close", "volume"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["ts"] = pd.to_datetime(df["ts"], unit="ms")
            return compute_features(df)
        except Exception as e:
            print(f"[ERROR] fetch_latest_candle Binance {symbol}: {e}")
            return None

    elif config.EXCHANGE == "bybit":
        url = (f"{_get_base_url()}{ep['klines_path']}"
               f"?category=linear&symbol={symbol}&interval=5&limit={config.CANDLE_LIMIT}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("result", {}).get("list", [])
            if not items:
                return None
            df = pd.DataFrame(items, columns=["ts", "open", "high", "low", "close", "volume", "turnover"])
            df = df.iloc[::-1]  # Orden cronológico (Bybit devuelve invertido)
            for c in ["open", "high", "low", "close", "volume"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["ts"] = pd.to_datetime(df["ts"].astype(int), unit="ms")
            return compute_features(df)
        except Exception as e:
            print(f"[ERROR] fetch_latest_candle Bybit {symbol}: {e}")
            return None

    return None


def scan_top_opportunities_live(progress_callback=None):
    """
    Escanea los top 100 y devuelve las 3 mejores señales.
    También retorna estadísticas del escaneo para diagnóstico.
    """
    symbols_or_error = fetch_top_symbols()

    # Si hubo error al obtener los símbolos
    if isinstance(symbols_or_error, dict) and "error" in symbols_or_error:
        error_msg = symbols_or_error["error"]
        if progress_callback:
            progress_callback(1.0, f"Error al obtener símbolos: {error_msg}")
        return [], {"scanned": 0, "errors": 1, "low_score": 0, "no_data": 0, "error_msg": error_msg}

    symbols = symbols_or_error
    if not symbols:
        if progress_callback:
            progress_callback(1.0, "No se pudieron obtener símbolos del exchange.")
        return [], {"scanned": 0, "errors": 1, "low_score": 0, "no_data": 0,
                     "error_msg": "Lista vacía de símbolos"}

    total = len(symbols)
    signals = []
    stats = {"scanned": 0, "errors": 0, "low_score": 0, "no_data": 0, "error_msg": ""}

    for i, sym in enumerate(symbols):
        if progress_callback:
            pct = (i + 1) / total
            progress_callback(pct, f"Escaneando {i+1}/{total}: {sym}...")

        df = fetch_latest_candle(sym)
        if df is None:
            stats["errors"] += 1
            continue
        if len(df) < 20:
            stats["no_data"] += 1
            continue

        stats["scanned"] += 1

        sig = generate_signal(df, threshold=config.SCORE_THRESHOLD)
        if sig["signal"] == "WAIT":
            stats["low_score"] += 1
            continue

        volatility = df["close"].pct_change().std()
        lev = optimal_leverage(sig["score"], volatility)
        next_min = estimate_next_signal(df)

        clean_sym = sym.replace("USDT", "")

        signals.append({
            "symbol": clean_sym,
            "signal": sig["signal"],
            "price": sig["price"],
            "score": sig["score"],
            "leverage": lev,
            "next_min": next_min,
            "timestamp": sig["timestamp"]
        })

        # Pequeña pausa para no saturar la API
        time.sleep(0.05)

    signals.sort(key=lambda x: x["score"], reverse=True)
    return signals[:3], stats
