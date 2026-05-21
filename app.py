import streamlit as st
import time
from scanner_engine import scan_top_opportunities_live
from audit_engine import audit_last_signal
from state_manager import save_last_signal, load_last_signal, append_audit_result
from data_loader import load_cached_data
from timing_engine import estimate_next_signal
import config

st.set_page_config(page_title="LEVIATHAN Multi‑Exchange Scanner", layout="wide")
st.title("🐋 LEVIATHAN – Scanner Multi‑Activo")

# --- Selección de exchange con botones ---
col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    if st.button("🔶 Binance"):
        config.EXCHANGE = "binance"
        st.success("Exchange cambiado a Binance")
with col2:
    if st.button("🔷 Bybit"):
        config.EXCHANGE = "bybit"
        st.success("Exchange cambiado a Bybit")
st.write(f"**Exchange actual:** `{config.EXCHANGE.upper()}`")

# --- Inicializar estado de señal activa ---
if "active_signal" not in st.session_state:
    st.session_state.active_signal = None       # dict de la señal vigente
    st.session_state.signal_expiry = None        # timestamp cuando expira
    st.session_state.signal_window_min = 5        # ventana de validez en minutos

# ========================
#  BOTÓN DE ESCANEO
# ========================
if st.button("🔍 Escanear Top 100"):
    # ---- Barra de progreso + marcador de tiempo ----
    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()

    # Actualizamos el estado del exchange por si se cambió
    top_signals, scan_log = scan_top_opportunities_live(
        progress_callback=lambda p, msg: (progress_bar.progress(p), status_text.text(msg))
    )

    elapsed = time.time() - start_time
    status_text.text(f"Escaneo completado en {elapsed:.1f} s — {len(top_signals)} señales encontradas")
    progress_bar.progress(1.0)

    if not top_signals:
        st.warning("No se encontraron señales por encima del umbral.")
        # Mostrar diagnóstico de lo que sí se escaneó
        with st.expander("🔍 Diagnóstico del escaneo"):
            st.write(f"Activos escaneados: {scan_log.get('scanned', 0)}")
            st.write(f"Errores de API: {scan_log.get('errors', 0)}")
            st.write(f"Señales descartadas (score bajo): {scan_log.get('low_score', 0)}")
            st.write(f"Activos sin datos suficientes: {scan_log.get('no_data', 0)}")
            st.caption("Si 'escaneados' es 0, verifica tu conexión o la API del exchange.")
    else:
        # ---- Guardar la mejor señal como señal activa ----
        best = top_signals[0]
        st.session_state.active_signal = best
        st.session_state.signal_expiry = time.time() + st.session_state.signal_window_min * 60

        st.success(f"✅ SEÑAL ACTIVA — {config.EXCHANGE.upper()}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Activo", best["symbol"])
        col2.metric("Dirección", best["signal"])
        col3.metric("Score", f"{best['score']:.1f}")
        col4.metric("Apalancamiento", f"{best['leverage']:.1f}x")
        st.write(f"💲 Precio de referencia: **${best['price']:.4f}**")
        st.write(f"⏳ Ventana de validez: **{st.session_state.signal_window_min} minutos** (caduca a las {time.strftime('%H:%M:%S', time.localtime(st.session_state.signal_expiry))})")
        st.write(f"🕐 Próxima señal estimada en: **{best['next_min']} minutos**")
        save_last_signal(best)

        # Tabla de las 3 mejores señales
        with st.expander(f"📋 Top 3 señales en {config.EXCHANGE.upper()}"):
            for i, sig in enumerate(top_signals, 1):
                cols = st.columns([1, 1, 1, 1, 2])
                cols[0].write(f"**#{i} {sig['symbol']}**")
                cols[1].write(f"{sig['signal']}")
                cols[2].write(f"Score: {sig['score']:.1f}")
                cols[3].write(f"⚡{sig['leverage']:.1f}x")
                cols[4].write(f"⏳ próx. señal: {sig['next_min']}min")

# ========================
#  MOSTRAR SEÑAL ACTIVA (si aún no expiró)
# ========================
if st.session_state.active_signal:
    remaining = st.session_state.signal_expiry - time.time()
    if remaining > 0:
        st.divider()
        st.subheader("🟢 SEÑAL ACTIVA VIGENTE")
        mins, secs = divmod(int(remaining), 60)
        st.info(f"⏰ **Tiempo restante para operar: {mins} min {secs} s** — Señal {st.session_state.active_signal['signal']} en {st.session_state.active_signal['symbol']} | Score: {st.session_state.active_signal['score']:.1f} | Apalancamiento: {st.session_state.active_signal['leverage']:.1f}x")
        st.caption("La señal se actualizará automáticamente al expirar.")
    else:
        # Expiró → WAIT
        st.session_state.active_signal = None
        st.session_state.signal_expiry = None
        st.divider()
        st.subheader("⏳ WAIT – Señal expirada")
        st.info("La ventana de validez terminó. Vuelve a escanear para obtener una nueva señal.")

# ========================
#  SI NO HAY SEÑAL ACTIVA → MOSTRAR ESTADO DEL MERCADO
# ========================
else:
    st.divider()
    st.subheader("⏳ ESTADO: SIN SEÑAL ACTIVA")
    st.info("Actualmente no hay ninguna señal vigente. El mercado no ha alcanzado el umbral de puntuación necesario (score ≥ 68).")
    st.write("Puedes presionar **'Escanear Top 100'** para reevaluar el mercado.")
    st.caption("La puntuación se calcula con EMA, RSI, volumen y pendiente de tendencia sobre los últimos 50 candles de 5 minutos.")

# ========================
#  AUDITORÍA DE ÚLTIMA SEÑAL
# ========================
st.divider()
st.subheader("📊 Auditoría de la última señal emitida")
last = load_last_signal()
if last:
    df = load_cached_data(last.get("symbol", "BTC"), "5m", 50)
    mask = df["ts"] > last["timestamp"]
    future_df = df[mask].head(6)
    audit = audit_last_signal(last, future_df)
    if audit:
        audit["signal"] = last["signal"]
        append_audit_result(audit)
        colA, colB = st.columns(2)
        colA.metric("Resultado", audit["result"], delta=f"{audit['pnl_pct']}%")
        colB.metric("Mov. favorable máx.", f"{audit['max_favorable']}%")
        st.write(f"Adverso máx.: {audit['max_adverse']}%")
    else:
        st.info("Aún no han transcurrido 30 minutos desde la última señal.")
else:
    st.info("No hay señal previa almacenada.")

# ========================
#  PIE DE PÁGINA
# ========================
st.divider()
st.caption(f"⏱️ Última actualización: {time.strftime('%H:%M:%S')} | Exchange: {config.EXCHANGE.upper()} | Umbral de score: {config.SCORE_THRESHOLD} | Apalancamiento: {config.LEVERAGE_MIN}x–{config.LEVERAGE_MAX}x")
