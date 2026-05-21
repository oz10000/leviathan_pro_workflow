import streamlit as st
from signal_engine import generate_signal
from timing_engine import estimate_next_signal
from audit_engine import audit_last_signal
from risk_engine import optimal_leverage
from state_manager import save_last_signal, load_last_signal, append_audit_result
from data_loader import load_cached_data

st.set_page_config(page_title="LEVIATHAN SIGNAL ENGINE", layout="wide")
st.title("🐋 LEVIATHAN SIGNAL ENGINE v1 – Señales + Auditoría Temporal")

if st.button("🔍 Analizar mercado"):
    df = load_cached_data("BTC", "5m", 500)

    # 1. Generate current signal
    signal = generate_signal(df)
    save_last_signal(signal)

    # 2. Estimate time until next signal
    next_min = estimate_next_signal(df)

    # 3. Audit previous signal
    last = load_last_signal()
    # Get subsequent data (simulated: next 6 candles of 5min = 30min)
    if last and "timestamp" in last:
        mask = df["ts"] > last["timestamp"]
        future_df = df[mask].head(6)
    else:
        future_df = df.iloc[:0]
    audit = audit_last_signal(last, future_df) if last else None
    if audit:
        audit["signal_timestamp"] = last["timestamp"]
        audit["signal"] = last["signal"]
        append_audit_result(audit)

    # ---- UI ----
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📡 SEÑAL ACTUAL")
        if signal["signal"] == "WAIT":
            st.warning("⏳ WAIT – No hay entrada clara")
        else:
            st.success(f"✅ {signal['signal']}")
        st.write(f"**Score:** {signal['score']:.1f}")
        st.write(f"**Precio de referencia:** ${signal['price']:.2f}")

        volatility = df["close"].pct_change().std()
        leverage = optimal_leverage(signal["score"], volatility)
        st.metric("⚡ Apalancamiento óptimo", f"{leverage:.1f}x")

    with col2:
        st.subheader("⏱️ CICLO TEMPORAL")
        st.write(f"⏳ Próxima señal estimada en: **{next_min} minutos**")
        st.caption("Basado en volatilidad y fuerza de tendencia")

    st.divider()
    st.subheader("📊 AUDITORÍA DE LA SEÑAL ANTERIOR")
    if audit:
        colA, colB = st.columns(2)
        colA.metric("Resultado", audit["result"], delta=audit["pnl_pct"])
        colB.metric("Variación máxima favorable", f"{audit['max_favorable']}%")
        st.write(f"Movimiento adverso máximo: {audit['max_adverse']}%")
    else:
        st.info("Aún no hay señal previa para auditar.")
