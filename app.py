import streamlit as st
from scanner_engine import scan_top_opportunities
from audit_engine import audit_last_signal
from state_manager import save_last_signal, load_last_signal, append_audit_result
from data_loader import load_cached_data
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

if st.button("🔍 Escanear Top 100"):
    with st.spinner("Analizando los 100 activos más líquidos..."):
        top_signals = scan_top_opportunities()
        if not top_signals:
            st.warning("No se encontraron señales por encima del umbral.")
        else:
            st.success(f"Señales detectadas en {config.EXCHANGE.upper()}:")
            for i, sig in enumerate(top_signals, 1):
                col1, col2 = st.columns([1, 2])
                col1.metric(f"#{i} {sig['symbol']}", sig['signal'], delta=f"Score {sig['score']:.1f}")
                col2.write(f"💲 {sig['price']:.4f}   ⚡ {sig['leverage']:.1f}x   ⏳ próx. {sig['next_min']}min")
                save_last_signal(sig)

    # Auditoría
    st.divider()
    st.subheader("📊 Auditoría de última señal")
    last = load_last_signal()
    if last:
        df = load_cached_data(last.get("symbol","BTC"), "5m", 50)
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
