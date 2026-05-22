import streamlit as st
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from scanner_engine import scan_top_opportunities_live, fetch_top_symbols, fetch_latest_candle
from signal_engine import generate_signal
from audit_engine import audit_last_signal
from state_manager import save_last_signal, load_last_signal
from data_loader import load_cached_data
import config

st.set_page_config(page_title="LEVIATHAN SIGNAL", layout="centered", initial_sidebar_state="collapsed")

# Soft dark theme
st.markdown(f"""
<style>
    .stApp {{
        background-color: {config.THEME_BG};
        color: {config.THEME_TEXT};
    }}
    .signal-box {{
        background-color: {config.THEME_CARD};
        border-radius: 16px;
        padding: 32px;
        margin: 24px 0;
        text-align: center;
    }}
    .signal-buy {{ color: {config.THEME_ACCENT}; font-weight: 700; font-size: 2rem; }}
    .signal-sell {{ color: #FF4D4D; font-weight: 700; font-size: 2rem; }}
    .timer {{ font-size: 1.6rem; font-weight: bold; color: #FFA500; }}
    .metric-label {{ font-size: 0.85rem; color: #8B94A3; text-transform: uppercase; letter-spacing: 0.05em; }}
    .metric-value {{ font-size: 1.3rem; font-weight: 600; color: {config.THEME_TEXT}; }}
    h2 {{ color: {config.THEME_ACCENT}; }}
    hr {{ border-color: #2E3345; }}
</style>
""", unsafe_allow_html=True)

st.title("🐋 LEVIATHAN SIGNAL")

col1, col2 = st.columns(2)
with col1:
    if st.button("🔶 Binance"):
        config.EXCHANGE = "binance"
with col2:
    if st.button("🔷 Bybit"):
        config.EXCHANGE = "bybit"
st.caption(f"Exchange: **{config.EXCHANGE.upper()}**")

if "active_signal" not in st.session_state:
    st.session_state.active_signal = None
    st.session_state.signal_expiry = None

# ==================== MAIN SCAN ====================
if st.button("🔍 Escanear Mercado", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(pct, msg):
        progress_bar.progress(pct)
        status_text.text(msg)

    with st.spinner("Escaneando los 100 activos más líquidos..."):
        top_signals, log = scan_top_opportunities_live(progress_callback=update_progress)

    progress_bar.empty()
    status_text.empty()

    if top_signals:
        best = top_signals[0]
        st.session_state.active_signal = best
        st.session_state.signal_expiry = time.time() + best.get("duration_min", 5) * 60
        save_last_signal(best)
        st.success(f"Señal certificada: **{best['signal']}** en **{best['symbol']}**")
    else:
        st.warning("No se encontraron señales que superen el umbral de calidad.")
        with st.expander("Diagnóstico"):
            st.write(f"Activos escaneados: {log.get('scanned', 0)}")
            st.write(f"Errores: {log.get('errors', 0)}")
            st.write(f"Descartados por score bajo: {log.get('low_score', 0)}")
            if log.get("error_msg"):
                st.error(log["error_msg"])

# ==================== ACTIVE SIGNAL DISPLAY ====================
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

        with st.expander("📋 Cómo ejecutar esta operación"):
            st.markdown("""
            1. Abre el exchange seleccionado (Binance/Bybit).
            2. Verifica que estás en la cuenta correcta (DEMO/LIVE).
            3. Busca el activo exacto.
            4. Configura: Entrada, Take Profit y Stop Loss según los valores de arriba.
            5. Ajusta el apalancamiento exactamente al recomendado.
            6. Revisa todos los datos antes de enviar la orden.
            7. Ejecuta manualmente y monitorea.

            ⚠️ Si el tiempo restante es muy corto, espera la próxima señal.
            """)
    else:
        st.session_state.active_signal = None
        st.session_state.signal_expiry = None
        st.info("Señal expirada. Escanea de nuevo.")
else:
    st.info("No hay señal activa. Presiona 'Escanear Mercado' para buscar una oportunidad.")

# ==================== MARKET RANKING (Top 5 without threshold) ====================
st.divider()
st.subheader("📊 Ranking de Mercado (informativo)")

if st.button("Actualizar ranking", use_container_width=True):
    with st.spinner("Calculando puntuaciones..."):
        syms = fetch_top_symbols()
        all_scores = []
        for sym in (syms[:30] if isinstance(syms, list) else []):
            df = fetch_latest_candle(sym)
            if df is not None and len(df) >= 20:
                raw = generate_signal(df, threshold=0)   # force generation for ranking
                if raw["signal"] != "WAIT":
                    is_certified = raw["score"] >= config.SCORE_THRESHOLD
                    all_scores.append({
                        "symbol": sym.replace("USDT", ""),
                        "direction": raw["signal"],
                        "score": raw["score"],
                        "price": raw["price"],
                        "certified": is_certified,
                        "tp": raw["price"] + (1 if raw["signal"]=="BUY" else -1) * config.TP_ATR * raw["atr"],
                        "sl": raw["price"] - (1 if raw["signal"]=="BUY" else -1) * config.SL_ATR * raw["atr"],
                    })
        all_scores.sort(key=lambda x: x["score"], reverse=True)
        top5 = all_scores[:5]

        if top5:
            for i, s in enumerate(top5, 1):
                cert_badge = "✅" if s["certified"] else "❌"
                st.write(f"{i}. {cert_badge} {s['symbol']} — {s['direction']} | Score: {s['score']:.1f} | Certificada: {'Sí' if s['certified'] else 'No'}")
            st.caption("✅ = Supera el umbral (68). ❌ = No supera el umbral. LEVIATHAN solo emite señales certificadas.")
        else:
            st.warning("No se pudo obtener puntuaciones.")

# ==================== AUDITORÍA ====================
st.divider()
st.subheader("📊 Auditoría de la última señal")
last = load_last_signal()
if last:
    try:
        last_ts = datetime.fromisoformat(last["timestamp"])
    except (ValueError, KeyError):
        st.warning("Timestamp no válido en la señal previa.")
        st.stop()

    df = load_cached_data(last.get("symbol", "BTC"), "5m", 50)
    mask = df["ts"] > last_ts
    future_df = df[mask].head(6)
    audit = audit_last_signal(last, future_df)

    if audit and "status" not in audit:
        cols = st.columns(2)
        result = audit.get("result", "N/A")
        pnl = audit.get("pnl_with_leverage", None)
        fav = audit.get("max_favorable", None)
        adv = audit.get("max_adverse", None)
        dur = audit.get("duration_min", None)

        cols[0].metric("Resultado", result)
        if pnl is not None:
            cols[1].metric("PnL teórico", f"{pnl}%")
        details = f"Favorable: +{fav}% | Adverso: {adv}% | Duración: {dur} min" if fav and adv and dur else "Datos incompletos."
        st.write(details)
    elif audit and audit.get("status") == "pending":
        st.write("Esperando datos futuros...")
    else:
        st.write("No se pudo auditar la señal anterior.")
else:
    st.write("Aún no hay señal previa almacenada.")

st.divider()
st.caption("LEVIATHAN — Terminal de señales manuales · Consistente · Simple · Profesional")
