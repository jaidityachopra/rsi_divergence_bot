import streamlit as st
st.set_page_config(page_title="RSI Bullish Divergence", layout="wide")
import pandas as pd
from datetime import date, timedelta
from main import get_bullish_divergence_results
from stock_list import stock_list as companies  # Ensure this is imported
from main import is_nse_trading_day

def highlight_returns(val):
    try:
        val_float = float(val)
        color = "green" if val_float > 0 else "red" if val_float < 0 else "black"
        return f"color: {color}"
    except:
        return ""

def run_analysis_with_progress(date_range, use_next_open=False):
    all_results = []
    total_iterations = len(date_range) * len(companies)
    current_iteration = 0

    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(done, total, symbol):
        nonlocal current_iteration
        current_iteration += 1
        progress = int((current_iteration / total_iterations) * 100)
        progress_bar.progress(progress)
        status_text.text(f"Analyzing {symbol} ({current_iteration}/{total_iterations})...")

    for dt in date_range:
        daily_results = get_bullish_divergence_results(
            dt.date(), progress_callback=update_progress, use_next_open=use_next_open
        )
        for r in daily_results:
            r["Date"] = dt.date()
            all_results.append(r)

    progress_bar.empty()
    status_text.empty()

    return all_results

# --- Streamlit UI ---

st.title("📈 RSI Bullish Divergence Detector")

# --- Date Range Selection ---
today = date.today()
one_year_ago = today - timedelta(days=365)

st.markdown("### Select a date range to analyze RSI divergence")
start_date, end_date = st.date_input(
    "Pick a range (up to 1 year)",
    value=(one_year_ago, today),
    min_value=one_year_ago,
    max_value=today
)

return_basis = st.radio(
    "Select basis for return calculation:",
    ("Close Price on Divergence Day", "Open Price Next Day"),
    index=0
)


if st.button("Run Analysis"):
    date_range = [dt for dt in pd.date_range(start=start_date, end=end_date)
              if is_nse_trading_day(dt.date())]

    if not date_range:
        st.warning("⚠️ Please select a valid date range.")
    else:
        use_next_open = (return_basis == "Open Price Next Day")
        all_results = run_analysis_with_progress(date_range, use_next_open)

        # if all_results:
        #     df = pd.DataFrame(all_results)
        #     df = df[["Date", "Symbol", "Prev Close", "Divergence Close", "RSI",
        #              "Day+1 Return (%)", "Day+2 Return (%)", "Day+3 Return (%)",
        #              "Day+4 Return (%)", "Day+5 Return (%)"]]

        #     st.success(f"✅ Found {len(df)} total bullish divergences.")

        #     return_cols = ["Day+1 Return (%)", "Day+2 Return (%)", "Day+3 Return (%)",
        #                    "Day+4 Return (%)", "Day+5 Return (%)"]
        #     all_cols = ["Prev Close", "Divergence Close", "RSI"] + return_cols

        #     styled_df = df.style\
        #         .applymap(highlight_returns, subset=return_cols)\
        #         .format({col: "{:.2f}" for col in all_cols})

        #     st.dataframe(styled_df, use_container_width=True)
        # else:
        #     st.warning("⚠️ No bullish divergences found in the selected range.")

        if all_results:
            df = pd.DataFrame(all_results)
            df = df[["Date", "Symbol", "Prev Close", "Divergence Close", "Open Next Day", "RSI",
             "Day+1 Return (%)", "Day+2 Return (%)", "Day+3 Return (%)",
             "Day+4 Return (%)", "Day+5 Return (%)"]]

            st.success(f"✅ Found {len(df)} total bullish divergences.")

            return_cols = ["Day+1 Return (%)", "Day+2 Return (%)", "Day+3 Return (%)",
                   "Day+4 Return (%)", "Day+5 Return (%)"]
            all_cols = ["Prev Close", "Divergence Close", "Open Next Day", "RSI"] + return_cols

            styled_df = df.style\
                .applymap(highlight_returns, subset=return_cols)\
                .format({col: "{:.2f}" for col in all_cols})

            st.dataframe(styled_df, use_container_width=True)

    # ---------------------- Historical Performance Analysis ----------------------
            st.markdown("### 📊 Historical Performance Analysis")
            st.info("This analysis shows how well past divergence signals performed across holding periods.")

            perf_data = []
            for col in return_cols:
                valid_returns = df[col].dropna()
                if not valid_returns.empty:
                    win_rate = (valid_returns > 0).mean() * 100
                    avg_return = valid_returns.mean()
                    median_return = valid_returns.median()
                else:
                    win_rate = avg_return = median_return = 0

                perf_data.append({
                    "Holding Period": col,
                    "Win Rate (%)": round(win_rate, 2),
                    "Average Return (%)": round(avg_return, 2),
                    "Median Return (%)": round(median_return, 2)
                })

            perf_df = pd.DataFrame(perf_data)

            st.dataframe(perf_df.style.format({
                "Win Rate (%)": "{:.2f}",
                "Average Return (%)": "{:.2f}",
                "Median Return (%)": "{:.2f}"
            }), use_container_width=True)

            st.markdown("#### 📈 Win Rate per Holding Period")
            st.bar_chart(perf_df.set_index("Holding Period")["Win Rate (%)"])
        else:
            st.warning("⚠️ No bullish divergences found in the selected range.")
