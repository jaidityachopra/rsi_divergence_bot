import yfinance as yf
import pandas as pd
import ta
import requests
from datetime import datetime
from stock_list import stock_list as companies
from nsepython import nse_holidays

# ---------------------------- SETTINGS ---------------------------- #
rsi_period = 14
pivot_lookback = 5

# ------------------------------------------------------------------ #
def is_today(index_date):
    return index_date.date() == datetime.now().date()

def is_nse_trading_day():
    today = datetime.today().date()
    if today.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    holidays = nse_holidays()
    return str(today) not in holidays

def download_data(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period='6mo')  # Checking for 6months
    if data.empty:
        raise ValueError(f"No data found for {symbol}")
    return data

def add_rsi(data, period):
    data['rsi'] = ta.momentum.RSIIndicator(data['Close'], window=period).rsi()
    return data

def find_pivot_lows(series, left=5, right=5):
    pivots = []
    for i in range(left, len(series) - right):
        if all(series.iloc[i] < series.iloc[i - j] for j in range(1, left + 1)) and \
           all(series.iloc[i] < series.iloc[i + j] for j in range(1, right + 1)):
            pivots.append(i)
    return pivots


def check_bullish_divergence(data, pivot_lows):
    divergences = []
    for i in range(1, len(pivot_lows)):
        curr, prev = pivot_lows[i], pivot_lows[i - 1]
        rsi_hl = data['rsi'].iloc[curr] > data['rsi'].iloc[prev]
        price_ll = data['Low'].iloc[curr] < data['Low'].iloc[prev]
        if rsi_hl and price_ll:
            divergences.append(curr)
    return divergences


def send_whatsapp_message(api_key, phone_number, message):
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={message}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        print("WhatsApp message sent successfully!")
    else:
        print("Failed to send WhatsApp message:", response.text)

# ---------------------------- MAIN LOGIC ---------------------------- #
# data = download_data(symbol)
# data = add_rsi(data, rsi_period)
# pivot_lows = find_pivot_lows(data['rsi'], pivot_lookback, pivot_lookback)
# divergences = check_bullish_divergence(data, pivot_lows)



# if divergences:
#     print(f"Bullish RSI Divergences detected for {symbol}:")
#     for idx in divergences:
#         date = data.index[idx].strftime('%Y-%m-%d')
#         rsi_val = data['rsi'].iloc[idx]
#         print(f"{date} | RSI: {rsi_val:.2f}")
#         # api_key = "YOUR_API_KEY"
#         # phone_number = "YOUR_PHONE_NUMBER"  # Format: 91XXXXXXXXXX (country code + number)
#         # message = f"Bullish RSI Divergence detected for {symbol} on {date} | RSI: {rsi_val:.2f}"
#         # send_whatsapp_message(api_key, phone_number, message)
# else:
#     print("No bullish divergence found today.")


if not is_nse_trading_day():
    print("Market is closed today. Exiting script.")
    exit()

for symbol in companies:
    try:
        data = download_data(symbol)
        data = add_rsi(data, rsi_period)
        pivot_lows = find_pivot_lows(data['rsi'], pivot_lookback, pivot_lookback)
        divergences = check_bullish_divergence(data, pivot_lows)

        for idx in divergences:
            index_date = data.index[idx]
            if is_today(index_date):
                # today_date = datetime.today().strftime('%Y-%m-%d')
                rsi_val = data['rsi'].iloc[idx]
                print(f"Bullish RSI Divergence detected for {symbol} on {index_date.strftime('%Y-%m-%d')} | RSI: {rsi_val:.2f}")
                # print(f"{today_date} | RSI: {rsi_val:.2f}")
                # api_key = "YOUR_API_KEY"
                # phone_number = "YOUR_PHONE_NUMBER"  # Format: 91XXXXXXXXXX (country code + number)
                # message = f"Bullish RSI Divergence detected for {symbol} on {date} | RSI: {rsi_val:.2f}"
                # send_whatsapp_message(api_key, phone_number, message)
    
    except Exception as e:
        print(f"Error processing {symbol}: {e}")