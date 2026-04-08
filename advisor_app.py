import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Advisor Pro")

# --- 2. SECURITY LAYER ---
def check_password():
    if "app_password" in st.secrets:
        password = st.secrets["app_password"]
    else:
        password = "admin"

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔒 Advisor Pro Login")
    pwd_input = st.text_input("Enter Access Key", type="password")
    if st.button("Unlock Dashboard"):
        if pwd_input == password:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("⛔ Access Denied")
    return False

if not check_password():
    st.stop()

# --- 3. WATCHLIST ---
st.sidebar.header("📋 Market Watch")
watchlist = {
    "Tata Motors": "TATAMOTORS.NS",
    "Reliance": "RELIANCE.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Zomato": "ZOMATO.NS",
    "Manappuram": "MANAPPURAM.NS"
}
selected_name = st.sidebar.selectbox("Select Asset", list(watchlist.keys()))
ticker = watchlist[selected_name]

# --- 4. LIGHTWEIGHT DATA ENGINE ---
def get_data(symbol):
    try:
        # Download Data
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if df.empty: return df
        
        # --- MANUAL INDICATOR MATH (No pandas-ta needed) ---
        
        # 1. RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI_14'] = 100 - (100 / (1 + rs))
        
        # 2. EMA (Exponential Moving Average)
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        # 3. Bollinger Bands
        sma = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['BB_UPPER'] = sma + (std * 2)
        df['BB_LOWER'] = sma - (std * 2)
        
        return df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame()

# --- 5. DASHBOARD ---
st.title(f"📈 {selected_name} ({ticker})")
df = get_data(ticker)

if not df.empty:
    # Latest Values
    close = df['Close'].iloc[-1]
    rsi = df['RSI_14'].iloc[-1]
    ema = df['EMA_20'].iloc[-1]
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Price", f"₹{close:.2f}", f"{df['Close'].pct_change().iloc[-1]*100:.1f}%")
    col2.metric("RSI Indicator", f"{rsi:.1f}", "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral")
    col3.metric("Trend (EMA)", "Bullish" if close > ema else "Bearish", f"Target: {ema:.2f}")
    
    # Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_UPPER'], line=dict(color='gray', width=1, dash='dot'), name='Upper Band'))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_LOWER'], line=dict(color='gray', width=1, dash='dot'), name='Lower Band'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='orange', width=1), name='20 EMA'))
    
    fig.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Telegram Alert Button
    st.markdown("---")
    if st.button(f"🚨 Send {selected_name} Signal"):
        if "telegram" in st.secrets:
            bot = st.secrets["telegram"]["bot_token"]
            chat = st.secrets["telegram"]["chat_id"]
            msg = f"SIGNAL: {ticker}\nPrice: {close:.2f}\nRSI: {rsi:.1f}"
            requests.post(f"https://api.telegram.org/bot{bot}/sendMessage", json={"chat_id": chat, "text": msg})
            st.success("Signal Sent!")
        else:
            st.warning("Telegram secrets not configured.")

else:
    st.warning("Waiting for data...")

