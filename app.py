import streamlit as st
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from scanner_engine import scan_top_opportunities_live
from audit_engine import audit_last_signal
from state_manager import save_last_signal, load_last_signal, append_audit_result
from data_loader import load_cached_data
import config

st.set_page_config(page_title="LEVIATHAN SIGNAL", layout="centered", initial_sidebar_state="collapsed")

# Tema oscuro profesional minimalista
st.markdown(f"""
<style>
    .stApp {{ background-color: #0E1117; color: #F0F2F6; }}
    .signal-box {{
        background-color: #1E2130; border-radius: 16px; padding: 24px;
        margin: 16px 0; text-align: center;
    }}
    .signal-buy {{ color: #00FFAA; font-weight: bold; font-size: 2rem; }}
    .signal-sell {{ color: #FF4D4D; font-weight: bold; font-size: 2rem; }}
    .timer {{ font-size: 1.5rem; font-weight: bold; color: #FFA500; }}
    .metric-label {{ font-size: 0.85rem; color: #888; }}
    .metric-value {{ font-size: 1.2rem; font-weight: bold; }}
    h2 {{ color: #00FFAA; }}
    hr {{ border-color: #2E3345; }}
    .step {{ padding: 6px 0; }}
</style>
""", unsafe_allow_html=True)

st.title("🐋 LEVIATHAN SIGNAL")

# Selección de exchange con botones compactos
col1, col2 = st.columns(2)
with col1:
    if st.button("🔶 Binance"):
        config.EXCHANGE = "binance"
with col2:
    if st.button("🔷 Bybit"):
        config.EXCHANGE = "bybit"
st.caption(f"Exchange: **{config.EXCHANGE.upper()}**")

# Inicializar estado de señal activa
if "active_signal" not in st.session_state:
    st.session_state.active_signal = None
    st.session_state.signal_expiry = None

# Botón de escaneo
if st.button("🔍 Escanear Mercado", use_container_width=True):
    with st.spinner("Escaneando los 100 activos más líquidos..."):
        top_signals, log = scan_top_opportunities_live(
            progress_callback=lambda p, msg: None  # sin barra, solo espera
        )
        if top_signals:
            best = top_signals[0]
            st.session_state.active_signal = best
            # Usar duración mínima 5 minutos si falta la clave
            st.session_state.signal_expiry = time.time() + best.get("duration_min", 5) * 60
            save_last_signal(best)
        else:
            st.warning("No se encontraron señales que cumplan los criterios.")

# Mostrar señal activa (solo si hay señal y el tiempo de expiración es válido)
if st.session_state.active_signal and st.session_state.signal_expiry is not None:
    sig = st.session_state.active_signal
    remaining = st.session_state.signal_expiry - time.time()
    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st_autorefresh(interval=1000, key="countdown")
        st.markdown(f"""
        <div class="signal-box">
            <p class="metric-label">ACTIVO</p>
            <p class="metric-value">{sig['symbol']}</p>
            <p class="metric-label">DIRECCIÓN</p>
            <p class="{'signal-buy' if sig['signal']=='BUY' else 'signal-sell'}">{sig['signal']}</p>
            <p class="metric-label">PRECIO DE ENTRADA</p>
            <p class="metric-value">${sig['price']:.4f}</p>
            <p class="metric-label">TAKE PROFIT</p>
            <p class="metric-value">${sig['tp']:.4f}</p>
            <p class="metric-label">STOP LOSS</p>
            <p class="metric-value">${sig['sl']:.4f}</p>
            <p class="metric-label">APALANCAMIENTO</p>
            <p class="metric-value">{sig['leverage']:.1f}x</p>
            <p class="metric-label">TIEMPO RESTANTE</p>
            <p class="timer">{mins} min {secs} s</p>
            <p class="metric-label">CONFIANZA</p>
            <p class="metric-value">{sig['confidence']:.0f}%</p>
        </div>
        """, unsafe_allow_html=True)

        # Instrucciones paso a paso
        with st.expander("✅ Cómo ejecutar esta operación"):
            st.markdown("""
            1. Abrir el exchange seleccionado.
            2. Verificar si estás en **DEMO** o **LIVE**.
            3. Buscar el activo exacto.
            4. Confirmar que el precio esté cerca de la entrada.
            5. Configurar: entrada, take profit, stop loss.
            6. Usar el apalancamiento recomendado.
            7. Revisar todos los datos y ejecutar manualmente.

            ⚠️ Si el tiempo restante es bajo, espera la próxima señal.
            """)
    else:
        # La señal expiró, limpiar estado
        st.session_state.active_signal = None
        st.session_state.signal_expiry = None
        st.info("La señal expiró. Vuelve a escanear.")
else:
    st.info("No hay señal activa. Escanea el mercado para recibir una oportunidad.")

# Auditoría simple de la última señal
st.divider()
st.subheader("📊 Auditoría de la última señal")
last = load_last_signal()
if last:
    try:
        last_ts = datetime.fromisoformat(last["timestamp"])
    except (ValueError, KeyError):
        st.warning("No se pudo leer el timestamp de la última señal.")
        st.stop()

    df = load_cached_data(last.get("symbol", "BTC"), "5m", 50)
    mask = df["ts"] > last_ts
    future_df = df[mask].head(6)
    audit = audit_last_signal(last, future_df)
    if audit:
        cols = st.columns(2)
        cols[0].metric("Resultado", audit["result"])
        cols[1].metric("PnL teórico", f"{audit['pnl_with_leverage']}%")
        st.write(f"Movimiento favorable: +{audit['max_favorable']}% | Adverso: {audit['max_adverse']}% | Duración: {audit.get('duration_min', 'N/A')} min")
    else:
        st.write("Esperando datos futuros para auditar...")
else:
    st.write("Aún no hay señal previa.")

st.divider()
st.caption("LEVIATHAN — Terminal de señales manuales · Parámetros validados por backtest de 30 días")
