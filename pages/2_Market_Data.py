import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Market Data",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.title("📊 Market Data")
st.write("Use this page to review recent stock price trends before choosing valuation assumptions.")

# -----------------------------
# Inputs
# -----------------------------
ticker = st.text_input("Stock Ticker", value="TSM").upper()

period = st.selectbox(
    "Select Price History Period",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)

# -----------------------------
# Pull Market Data
# -----------------------------
@st.cache_data(ttl=3600)
def get_stock_history(stock_ticker, selected_period):
    try:
        stock = yf.Ticker(stock_ticker)
        data = stock.history(period=selected_period)

        if data is not None and not data.empty:
            return data
        return None
    except Exception:
        return None

data = get_stock_history(ticker, period)

# -----------------------------
# Display Market Data
# -----------------------------
if data is not None:
    latest_price = data["Close"].iloc[-1]
    starting_price = data["Close"].iloc[0]
    period_return = ((latest_price - starting_price) / starting_price) * 100
    high_price = data["High"].max()
    low_price = data["Low"].min()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Latest Close Price", f"${latest_price:,.2f}")
    col2.metric("Starting Price", f"${starting_price:,.2f}")
    col3.metric("Return Over Period", f"{period_return:,.2f}%")
    col4.metric("Price Range", f"${low_price:,.2f} - ${high_price:,.2f}")

    chart_data = data.reset_index()

    st.subheader(f"{ticker} Closing Price Chart")

    fig = px.line(
        chart_data,
        x="Date",
        y="Close",
        title=f"{ticker} Closing Price Over {period}",
        markers=False
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Trading Data")
    recent_data = data.tail(10)[["Open", "High", "Low", "Close", "Volume"]]

    st.dataframe(recent_data.style.format({
        "Open": "${:,.2f}",
        "High": "${:,.2f}",
        "Low": "${:,.2f}",
        "Close": "${:,.2f}",
        "Volume": "{:,.0f}"
    }))

    st.subheader("Why This Matters for Valuation")

    st.info("""
    Market data helps users compare the stock's current price behavior to the intrinsic value estimated in the DCF model.
    If a stock has increased significantly, investors may use more conservative assumptions.
    If the stock price has fallen, users may investigate whether the decline is temporary or connected to weaker fundamentals.
    """)

else:
    st.error("Market data could not be loaded. Try refreshing the app, changing the ticker, or using the Valuation page manual price input.")
