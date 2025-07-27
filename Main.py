import os
import time
import requests
import ccxt
import telegram
import ta
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
COINS = os.getenv("COINS", "BTC,ETH").split(",")
INTERVAL = int(os.getenv("INTERVAL_MINUTES", 60))

bot = telegram.Bot(token=TELEGRAM_TOKEN)
binance = ccxt.binance()
mexc = ccxt.mexc()

def get_ohlcv(symbol, exchange):
    try:
        return exchange.fetch_ohlcv(symbol, timeframe='1h')[-100:]
    except Exception as e:
        print(f"Error fetching OHLCV for {symbol} on {exchange.name}: {e}")
        return []

def analyze(data):
    try:
        close = [x[4] for x in data]
        ema = EMAIndicator(pd.Series(close), window=20).ema_indicator().iloc[-1]
        rsi = RSIIndicator(pd.Series(close), window=14).rsi().iloc[-1]
        macd = MACD(pd.Series(close)).macd_diff().iloc[-1]
        signal = "🔴 Sell" if rsi > 70 and macd < 0 else "🟢 Buy" if rsi < 30 and macd > 0 else "⚪️ Wait"
        return signal, round(rsi, 2)
    except:
        return "❌ Error", 0

def get_fear_and_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/").json()
        return r["data"][0]["value"], r["data"][0]["value_classification"]
    except:
        return "N/A", "Unknown"

def run():
    while True:
        message = f"📊 Market Signal\n\n"
        for coin in COINS:
            for ex in [binance, mexc]:
                symbol = f"{coin}/USDT"
                data = get_ohlcv(symbol, ex)
                if data:
                    signal, rsi = analyze(data)
                    message += f"{coin} ({ex.name}): {signal} (RSI: {rsi})\n"

        fear_value, fear_desc = get_fear_and_greed()
        message += f"\n😨 Fear & Greed Index: {fear_value} ({fear_desc})"

        bot.send_message(chat_id=CHAT_ID, text=message)
        time.sleep(INTERVAL * 60)

if __name__ == "__main__":
    import pandas as pd
    run()
