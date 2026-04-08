import streamlit as st
import yfinance as yf
import pandas_ta as ta
import plotly.graph_objects as go
import requests

# --- 1. SECURITY LAYER ---
def check_password():
    """Protects the app with a password screen."""
    if "app_password" in st.secrets:
        password = st.secrets["app_password"]
    else:
        password = "admin"  # Fallback for local testing

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔒 Advisor Pro Terminal")
    pwd_input = st.text_input("Enter Access Key", type="password")
    if st.button("Login"):
        if pwd_input == password:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("⛔ Access Denied")
    return False

if not check_password():
    st.stop()

# --- 2. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Advisor Pro")

# --- 3. SIDEBAR: WATCHLIST & ALERTS ---
st.sidebar.header("📋 Market Watch")
watchlist = {
    "Tata Motors": "TATAMOTORS.NS",
    "Manappuram": "MANAPPURAM.NS",
    "Reliance": "RELIANCE.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Zomato": "ZOMATO.NS"
}
selected_name = st.sidebar.selectbox("Select Asset", list(watchlist.keys()))
ticker = watchlist[selected_name]

st.sidebar.markdown("---")
st.sidebar.header("🔔 Telegram Config")
if "telegram" in st.secrets:
    bot_token = st.secrets["telegram"]["bot_token"]
    chat_id = st.secrets["telegram"]["chat_id"]
    st.sidebar.success("🔒 Secured via Cloud")
else:
    bot_token = st.sidebar.text_input("Bot Token", type="password")
    chat_id = st.sidebar.text_input("Chat ID")

# --- 4. ANALYSIS ENGINE ---
st.title(f"📈 {selected_name} ({ticker})")

try:
    # Fetch Data
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    
    if not df.empty:
        # Calculate Indicators
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        current_price = df['Close'].iloc[-1]
        rsi = df['RSI_14'].iloc[-1]
        
        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Price", f"₹{current_price:.2f}", f"{df['Close'].pct_change().iloc[-1]*100:.1f}%")
        c2.metric("RSI Strength", f"{rsi:.1f}", "Overbought" if rsi > 70 else "Neutral")
        
        # Charting
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
        fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Alert Button
        if st.button(f"⚠️ Send '{selected_name}' Alert"):
            if bot_token and chat_id:
                msg = f"🚨 ALERT: {selected_name} at ₹{current_price:.2f}\nRSI: {rsi:.1f}"
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": msg})
                st.toast("Signal Sent to Phone!")
            else:
                st.error("Missing Telegram Keys")
    else:
        st.error("No data found. Market may be closed.")

except Exception as e:
    st.error(f"System Error: {e}")
