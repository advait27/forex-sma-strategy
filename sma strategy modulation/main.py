import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime

# === Indicator Functions ===
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def generate_mock_data(rows=100, seed=42):
    np.random.seed(seed)
    time = pd.date_range(end=datetime.datetime.now(), periods=rows, freq='min')
    close = np.cumsum(np.random.randn(rows)) + 100
    volume = np.random.randint(100, 1000, size=rows)
    return pd.DataFrame({'datetime': time, 'close': close, 'volume': volume})

# === Streamlit App ===
st.set_page_config(page_title="Modular Forex Bot", layout="wide")
st.title("Directional Forex Strategy Bot (SMA + RSI + Volume)")

# Currency Pair Selector
currency_pairs = ["EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "NZD/USD", "USD/CHF"]
selected_pair = st.selectbox("Select Currency Pair", currency_pairs)

# Inputs
use_sma = st.checkbox("Enable SMA Crossover", value=True)
use_rsi = st.checkbox("Enable RSI Filter", value=True)
use_vol = st.checkbox("Enable Volume Filter", value=True)

sma_short_len = st.slider("SMA Short Length", 5, 50, 20)
sma_long_len = st.slider("SMA Long Length", 10, 100, 50)
rsi_len = st.slider("RSI Period", 5, 30, 14)
rsi_ob = st.slider("RSI Overbought", 60, 90, 70)
rsi_os = st.slider("RSI Oversold", 10, 40, 30)
vol_ma_len = st.slider("Volume MA Length", 5, 50, 20)

if st.button("Run Strategy"):
    # Use selected_pair as seed for reproducibility based on symbol
    seed = abs(hash(selected_pair)) % (2**32)
    df = generate_mock_data(seed=seed)

    # Compute indicators
    df['sma_short'] = df['close'].rolling(sma_short_len).mean()
    df['sma_long'] = df['close'].rolling(sma_long_len).mean()
    df['rsi'] = compute_rsi(df['close'], rsi_len)
    df['vol_ma'] = df['volume'].rolling(vol_ma_len).mean()

    # Strategy logic
    sma_cond = df['sma_short'] > df['sma_long'] if use_sma else True
    rsi_cond_b = df['rsi'] < rsi_ob if use_rsi else True
    rsi_cond_s = df['rsi'] > rsi_os if use_rsi else True
    vol_cond = df['volume'] > df['vol_ma'] if use_vol else True

    df['buy_signal'] = sma_cond & rsi_cond_b & vol_cond
    df['sell_signal'] = ~sma_cond & rsi_cond_s & vol_cond

    st.subheader(f"🔍 Trade Signals for {selected_pair}")
    latest_signal = "Hold"
    if df['buy_signal'].iloc[-1]:
        latest_signal = "BUY"
    elif df['sell_signal'].iloc[-1]:
        latest_signal = "SELL"
    st.success(f"Latest Signal: {latest_signal}")

    # Plotting
    st.subheader("📈 Price Chart with SMAs")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['datetime'], df['close'], label='Close', color='black')
    if use_sma:
        ax.plot(df['datetime'], df['sma_short'], label='SMA Short', color='orange')
        ax.plot(df['datetime'], df['sma_long'], label='SMA Long', color='blue')
    ax.scatter(df[df['buy_signal']]['datetime'], df[df['buy_signal']]['close'], label='BUY', color='green', marker='^')
    ax.scatter(df[df['sell_signal']]['datetime'], df[df['sell_signal']]['close'], label='SELL', color='red', marker='v')
    ax.legend()
    st.pyplot(fig)

    st.subheader("📊 RSI")
    fig2, ax2 = plt.subplots(figsize=(12, 2))
    ax2.plot(df['datetime'], df['rsi'], label='RSI', color='orange')
    ax2.axhline(rsi_ob, color='red', linestyle='--')
    ax2.axhline(rsi_os, color='green', linestyle='--')
    ax2.set_ylim(0, 100)
    st.pyplot(fig2)

    st.subheader("📋 Data Preview")
    st.dataframe(df[['datetime', 'close', 'volume', 'sma_short', 'sma_long', 'rsi', 'vol_ma', 'buy_signal', 'sell_signal']].tail(10))

st.info("Note: This simulation uses mock data. For real-time Forex data, connect an API like OANDA, Alpaca, or Binance.")
