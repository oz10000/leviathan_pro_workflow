# LEVIATHAN SIGNAL ENGINE — Configuración central

# Exchange por defecto: "binance" o "bybit"
EXCHANGE = "binance"

# Claves API (solo necesarias si se usan endpoints privados; el scanner usa públicos)
API_KEY = ""
API_SECRET = ""
PASSPHRASE = ""

# ==================== PARÁMETROS DEL MOTOR DE SEÑAL ====================
SCORE_THRESHOLD = 68              # Umbral mínimo para emitir BUY/SELL
TOP_N = 100                       # Número de activos a escanear (top por volumen)
LEVERAGE_MIN = 5                  # Apalancamiento mínimo
LEVERAGE_MAX = 8                  # Apalancamiento máximo
RISK_PER_TRADE = 0.04             # Riesgo por operación (4% del capital)

# ==================== INDICADORES Y PESOS ====================
W_TREND = 0.30
W_MOMENTUM = 0.25
W_VOL_EFF = 0.25
W_VOLUME = 0.20

# ==================== TEMPORALIDADES Y DATOS ====================
DEFAULT_TIMEFRAME = "5m"          # Timeframe principal
AUDIT_WINDOW_MINUTES = 30         # Ventana para auditar una señal pasada (en minutos)
CANDLE_LIMIT = 50                 # Velas descargadas para calcular indicadores

# ==================== SIMULACIÓN / BACKTEST ====================
INITIAL_CAPITAL = 100.0
MAX_TRADES = 30

# ==================== ESTADO Y LOGS ====================
STATE_FILE = "last_signal.json"
HISTORY_FILE = "audit_history.json"
