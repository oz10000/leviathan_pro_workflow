import streamlit as st
from scanner_engine import scan_top_opportunities, EXCHANGE as current_exchange
from audit_engine import audit_last_signal
from state_manager import save_last_signal, load_last_signal, append_audit_result
from data_loader import load_cached_data
import pandas as pd

st.set_page_config(page_title="LEVIATHAN Multi‑Exchange Scanner", layout="wide")
st.title("🐋 LEVIATHAN – Scanner Multi‑Activo")

# Selector de exchange
exchange = st.selectbox("Exchange", ["binance", "bybit"], index=0 if current_exchange=="binance" else 1)
if exchange != current_exchange:
    # Actualizar configuración en caliente
    from config import EXCHANGE as cfg_exchange
    cfg_exchange = exchange
    # En un script real, se modificaría config.py; aquí solo para la demo.

if st.button("🔍 Escanear Top 100"):
    with st.spinner("Analizando los 100 activos más líquidos..."):
        top_signals = scan_top_opportunities()
        if not top_signals:
            st.warning("No se encontraron señales por encima del umbral.")
        else:
            st.success(f"Señales detectadas en {exchange.upper()}:")
            for i, sig in enumerate(top_signals, 1):
                col1, col2 = st.columns([1, 2])
                col1.metric(f"#{i} {sig['symbol']}", sig['signal'], delta=f"Score {sig['score']:.1f}")
                col2.write(f"💲 {sig['price']:.4f}   ⚡ {sig['leverage']:.1f}x   ⏳ próx. {sig['next_min']}min")
                # Guardar señal para auditoría futura (opcional)
                save_last_signal(sig)

    # Auditoría de la última señal almacenada (de cualquier activo)
    st.divider()
    st.subheader("📊 Auditoría de última señal")
    last = load_last_signal()
    if last:
        # Cargar datos posteriores (simulado con data_loader)
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
