import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from datetime import datetime

exchange = ccxt.bybit()

def fetch_ohlcv(symbol, timeframe='1h', limit=200):
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def calculate_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def is_sideways(df, days=3, tolerance=0.03):
    recent = df[-days*24:]
    high = recent['high'].max()
    low = recent['low'].min()
    return (high - low) / low < tolerance

def detect_breakout(df):
    rsi = calculate_rsi(df['close'])
    df['RSI'] = rsi
    last_rsi = rsi.iloc[-1]
    prev_rsi = rsi.iloc[-2]

    recent_high = df['high'][-48:-1].max()
    last_close = df['close'].iloc[-1]
    last_volume = df['volume'].iloc[-1]
    avg_volume = df['volume'][-48:-1].mean()

    breakout = last_close > recent_high and last_volume > 1.5 * avg_volume and last_rsi > 60 and last_rsi > prev_rsi
    take_profit = last_rsi > 70 and last_rsi < prev_rsi

    return breakout, take_profit

def plot_chart(df, symbol):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
    df['RSI'] = calculate_rsi(df['close'])

    ax1.plot(df.index, df['close'], label='Close')
    ax1.set_title(f'{symbol} Price')
    ax1.legend()

    ax2.plot(df.index, df['RSI'], label='RSI', color='orange')
    ax2.axhline(70, color='red', linestyle='--')
    ax2.axhline(30, color='green', linestyle='--')
    ax2.set_title('RSI')
    ax2.legend()

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

def scan_market():
    signals = []
    markets = exchange.load_markets()
    usdt_pairs = [s for s in markets if s.endswith("/USDT")]

    for symbol in usdt_pairs:
        try:
            df = fetch_ohlcv(symbol)
            if is_sideways(df, days=3):
                breakout, _ = detect_breakout(df)
                if breakout:
                    buf = plot_chart(df, symbol)
                    current_price = df['close'].iloc[-1]
                    signals.append((symbol, current_price, buf))
        except Exception as e:
            print(f"[❌] Lỗi {symbol}: {e}")
    return signals

def check_one(symbol):
    try:
        df = fetch_ohlcv(symbol)
        if is_sideways(df, days=3):
            breakout, _ = detect_breakout(df)
            if breakout:
                buf = plot_chart(df, symbol)
                current_price = df['close'].iloc[-1]
                return (symbol, current_price, buf)
    except Exception as e:
        print(f"[❌] Lỗi khi kiểm tra {symbol}: {e}")
    return None
