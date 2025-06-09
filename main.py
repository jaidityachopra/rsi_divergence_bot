import yfinance as yf
import pandas as pd
import ta
import requests
from datetime import datetime
from stock_list import stock_list as companies
from nsepython import nse_holidays
import os
import streamlit as st

# api_key = os.getenv("CALLMEBOT_API_KEY")
# phone_number = os.getenv("PHONE_NUMBER")
# if not api_key or not phone_number:
#     raise ValueError("Please set the environment variables CALLMEBOT_API_KEY and PHONE_NUMBER.")

# ---------------------------- SETTINGS ---------------------------- #
rsi_period = 14
pivot_lookback = 5
TEST_DATE = datetime(2024, 12, 20).date()  # Change this to any known date
# ------------------------------------------------------------------ #
def is_today(index_date):
    # return index_date.date() == datetime.now().date()
    return index_date.date() == TEST_DATE

# Cache NSE holidays only once at startup
NSE_HOLIDAYS = set(nse_holidays())  # Store as set for fast lookup

def is_nse_trading_day(check_date=None):
    if check_date is None:
        check_date = datetime.today().date()
    if check_date.weekday() >= 5:
        return False
    return str(check_date) not in NSE_HOLIDAYS
@st.cache_data(ttl=86400)  # cache for 1 day
def download_data(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period='1y')  # Checking for 6months
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


@st.cache_data(ttl=86400)  # cache for 1 day
def get_preprocessed_data(symbol):
    data = download_data(symbol)
    data = add_rsi(data, rsi_period)
    pivot_lows = find_pivot_lows(data['rsi'], pivot_lookback, pivot_lookback)
    divergences = check_bullish_divergence(data, pivot_lows)
    return data, divergences



def send_whatsapp_message(api_key, phone_number, message):
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone_number}&text={message}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        print("WhatsApp message sent successfully!")
    else:
        print("Failed to send WhatsApp message:", response.text)


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

                # Send WhatsApp notification
                # message = f"Bullish RSI Divergence detected for {symbol} on {index_date.strftime('%d-%m-%Y')} | RSI: {rsi_val:.2f}"
                # send_whatsapp_message(api_key, phone_number, message)
    
    except Exception as e:
        print(f"Error processing {symbol}: {e}")











# def get_bullish_divergence_results(date):
#     results = []

#     for symbol in companies:
#         try:
#             data = download_data(symbol)
#             data = add_rsi(data, rsi_period)
#             pivot_lows = find_pivot_lows(data['rsi'], pivot_lookback, pivot_lookback)
#             divergences = check_bullish_divergence(data, pivot_lows)

#             for idx in divergences:
#                 index_date = data.index[idx].date()
#                 if index_date == date:
#                     rsi_val = data['rsi'].iloc[idx]
#                     close_today = data['Close'].iloc[idx]
#                     close_prev = data['Close'].iloc[idx - 1] if idx > 0 else None

#                     # Future returns
#                     future_returns = {}
#                     for i in range(1, 6):
#                         if idx + i < len(data):
#                             future_close = data['Close'].iloc[idx + i]
#                             ret = ((future_close - close_today) / close_today) * 100
#                             future_returns[f"Day+{i} Return (%)"] = round(ret, 2)

#                     result = {
#                         "Symbol": symbol,
#                         "Prev Close": round(close_prev, 2) if close_prev else None,
#                         "Divergence Close": round(close_today, 2),
#                         "RSI": round(rsi_val, 2),
#                         **future_returns
#                     }

#                     results.append(result)
#         except Exception as e:
#             print(f"Error processing {symbol}: {e}")

#     return results


def get_bullish_divergence_results(date, symbols=None, progress_callback=None, use_next_open=False):
    results = []
    symbols = symbols if symbols else companies
    total = len(symbols)

    for i, symbol in enumerate(symbols):
        try:
            data, divergences = get_preprocessed_data(symbol)

            for idx in divergences:
                index_date = data.index[idx].date()
                if index_date == date:
                    rsi_val = data['rsi'].iloc[idx]
                    close_today = data['Close'].iloc[idx]
                    close_prev = data['Close'].iloc[idx - 1] if idx > 0 else None

                    # Select base price for return calculation
                    # Get opening price of the next day (if available)
                    open_next_day = data['Open'].iloc[idx + 1] if idx + 1 < len(data) else None

                    # Select base price for return calculation
                    if use_next_open and open_next_day is not None:
                        base_price = open_next_day
                        price_basis = "Open Next Day"
                    else:
                        base_price = close_today
                        price_basis = "Close"


                    # Future returns based on selected base price
                    future_returns = {}
                    for j in range(1, 6):
                        if idx + j < len(data):
                            future_close = data['Close'].iloc[idx + j]
                            ret = ((future_close - base_price) / base_price) * 100
                            future_returns[f"Day+{j} Return (%)"] = round(ret, 2)

                    result = {
                        "Symbol": symbol,
                        "Prev Close": round(close_prev, 2) if close_prev else None,
                        "Divergence Close": round(close_today, 2),
                        "Open Next Day": round(open_next_day, 2) if open_next_day is not None else None,
                        "RSI": round(rsi_val, 2),
                        "Used Price": price_basis,
                        **future_returns
                    }

                    results.append(result)

        except Exception as e:
            print(f"Error processing {symbol}: {e}")
        
        if progress_callback:
            progress_callback(i + 1, total, symbol)

    return results
