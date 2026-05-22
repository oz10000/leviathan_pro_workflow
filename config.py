# LEVIATHAN SIGNAL ENGINE — Configuración central

# Exchange por defecto: "binance" o "bybit"
EXCHANGE = "binance"

# Claves API (solo necesarias si se usan endpoints privados; el scanner usa públicos)
API_KEY = ""
API_SECRET = ""
PASSPHRASE = ""

# ==================== ENDPOINTS SIN RESTRICCIÓN GEOGRÁFICA ====================
# Streamlit Cloud está alojado en EEUU. Binance.com y Bybit.com bloquean IPs de EEUU.
# Para endpoints públicos de solo lectura, ambos exchanges ofrecen dominios alternativos:
#   - Binance: data-api.binance.vision
#   - Bybit:   api.bytick.com

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

# ==================== FILTROS DE CALIDAD DE ACTIVO ====================
MIN_VOLUME_USD = 5_000_000        # volumen mínimo en USD en 24h
MAX_SPREAD_PCT = 0.5               # spread máximo permitido en porcentaje

# ==================== PARÁMETROS DEL MOTOR DE SEÑAL ====================
SCORE_THRESHOLD = 68               # Umbral mínimo para emitir BUY/SELL
TOP_N = 100                        # Número de activos a escanear (top por volumen)
LEVERAGE_MIN = 5                   # Apalancamiento mínimo
LEVERAGE_MAX = 8                   # Apalancamiento máximo
RISK_PER_TRADE = 0.04              # Riesgo por operación (4% del capital)

# ==================== INDICADORES Y PESOS ====================
W_TREND = 0.30
W_MOMENTUM = 0.25
W_VOL_EFF = 0.25
W_VOLUME = 0.20

# ==================== TEMPORALIDADES Y DATOS ====================
DEFAULT_TIMEFRAME = "5m"           # Timeframe principal
AUDIT_WINDOW_MINUTES = 30          # Ventana para auditar una señal pasada (en minutos)
CANDLE_LIMIT = 50                  # Velas descargadas para calcular indicadores

# ==================== TAKE PROFIT / STOP LOSS (validado por backtest) ====================
TP_ATR = 2.5                       # Multiplicador del ATR para take profit
SL_ATR = 0.7                       # Multiplicador del ATR para stop loss

# ==================== SIMULACIÓN / BACKTEST ====================
INITIAL_CAPITAL = 100.0
MAX_TRADES = 30

# ==================== ESTADO Y LOGS ====================
STATE_FILE = "last_signal.json"
HISTORY_FILE = "audit_history.json"
