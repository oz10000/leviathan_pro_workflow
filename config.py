# LEVIATHAN SIGNAL ENGINE — Configuración central

EXCHANGE = "binance"

ENDPOINTS = {
    "binance": {
        "base_url": "https://data-api.binance.vision",
        "ticker_path": "/api/v3/ticker/24hr",
        "klines_path": "/api/v3/klines",
    },
    "bybit": {
        "base_url": "https://api.bytick.com",
        "ticker_path": "/v5/market/tickers",
        "klines_path": "/v5/market/kline",
    },
}

# Filtros de calidad
MIN_VOLUME_USD = 5_000_000
MAX_SPREAD_PCT = 0.5

# Activos basura (stablecoins / pares sintéticos)
BLACKLIST = [
    "USDCUSDT", "BUSDUSDT", "FDUSDUSDT", "TUSDUSDT", "USD1USDT",
    "USDPUSDT", "DAIUSDT", "USTCUSDT", "LUNCUSDT", "PAXUSDT"
]

SCORE_THRESHOLD = 68
TOP_N = 100
LEVERAGE_MIN = 5
LEVERAGE_MAX = 8
RISK_PER_TRADE = 0.04
W_TREND = 0.30
W_MOMENTUM = 0.25
W_VOL_EFF = 0.25
W_VOLUME = 0.20
DEFAULT_TIMEFRAME = "5m"
AUDIT_WINDOW_MINUTES = 30
CANDLE_LIMIT = 50
TP_ATR = 2.5
SL_ATR = 0.7
INITIAL_CAPITAL = 100.0
MAX_TRADES = 30
STATE_FILE = "last_signal.json"
HISTORY_FILE = "audit_history.json"

# Colores del tema (gris oscuro suave, profesional)
THEME_BG = "#1A1D24"
THEME_CARD = "#232830"
THEME_TEXT = "#E0E4EA"
THEME_ACCENT = "#00D2A1"
