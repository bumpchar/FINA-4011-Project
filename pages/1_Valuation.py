import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

st.set_page_config(
    page_title="DCF Valuation",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%);
}
</style>
""", unsafe_allow_html=True)

st.title("📈 DCF Valuation Model")
st.write("Estimate a stock’s intrinsic value using real company data and realistic assumptions.")

st.sidebar.header("Valuation Inputs")

ticker = st.sidebar.text_input("Stock Ticker", value="TSM").upper()


# -----------------------------
# MARKET PRICE (FIXED VERSION)
# -----------------------------
@st.cache_data(ttl=300)
def get_market_price(stock_ticker):
    try:
        stock = yf.Ticker(stock_ticker)

        # fast + reliable
        price = stock.fast_info.get("last_price", None)

        if price is not None:
            return float(price)

        # fallback
        price_data = stock.history(period="1d")
        if not price_data.empty:
            return float(price_data["Close"].iloc[-1])

        return None

    except Exception:
        return None


# -----------------------------
# YAHOO DATA
# -----------------------------
@st.cache_data(ttl=3600)
def get_yahoo_data(stock_ticker):
    try:
        stock = yf.Ticker(stock_ticker)
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        info = stock.info
        return income_stmt, balance_sheet, info
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), {}


def get_value(statement, labels):
    for label in labels:
        if label in statement.index:
            vals = statement.loc[label].dropna()
            if not vals.empty:
                return float(vals.iloc[0]) / 1_000_000
    return None


def get_series(statement, labels):
    for label in labels:
        if label in statement.index:
            return statement.loc[label].dropna() / 1_000_000
    return pd.Series(dtype=float)


# -----------------------------
# LOAD DATA
# -----------------------------
current_price = get_market_price(ticker)
income_stmt, balance_sheet, info = get_yahoo_data(ticker)


# -----------------------------
# MARKET PRICE UI
# -----------------------------
st.sidebar.subheader("Market Price")

use_manual_price = st.sidebar.checkbox(
    "Use manual market price",
    value=False
)

manual_price = st.sidebar.number_input(
    "Manual Market Price ($)",
    value=250.00,
    step=1.00
)

if use_manual_price or current_price is None:
    final_price = manual_price
else:
    final_price = current_price

if current_price is None:
    st.sidebar.error("Could not load live price — using manual input.")
else:
    st.sidebar.success(f"Live price: ${current_price:,.2f}")


# -----------------------------
# LOCKED INPUTS
# -----------------------------
starting_revenue = get_value(income_stmt, ["Total Revenue"]) or 90000
debt = get_value(balance_sheet, ["Total Debt"]) or 30000
cash = get_value(balance_sheet, ["Cash And Cash Equivalents"]) or 50000

shares_outstanding = info.get("sharesOutstanding")
if shares_outstanding:
    shares_outstanding = shares_outstanding / 1_000_000
else:
    shares_outstanding = 5186


st.sidebar.subheader("Operating Assumptions")

st.sidebar.metric("Starting Revenue", f"${starting_revenue:,.0f}M")
st.sidebar.caption("Locked from Yahoo Finance")


# -----------------------------
# HISTORICAL DATA
# -----------------------------
rev = get_series(income_stmt, ["Total Revenue"])
ebit = get_series(income_stmt, ["Operating Income"])
tax = get_series(income_stmt, ["Tax Provision"])
pretax = get_series(income_stmt, ["Pretax Income"])


# Growth
growth_hist = rev.pct_change().dropna()
growth_avg = growth_hist.mean() if not growth_hist.empty else 0.10

growth_rate = st.sidebar.slider(
    "Revenue Growth (%)",
    0.0, 25.0,
    float(round(growth_avg * 100, 1)),
    0.5
) / 100

st.sidebar.caption(f"Avg: {growth_avg:.1%}")


# EBIT margin
margin_hist = (ebit / rev).dropna()
margin_avg = margin_hist.mean() if not margin_hist.empty else 0.45

ebit_margin = st.sidebar.slider(
    "EBIT Margin (%)",
    20.0, 60.0,
    float(round(margin_avg * 100, 1)),
    0.5
) / 100

st.sidebar.caption(f"Avg: {margin_avg:.1%}")


# Tax rate
tax_hist = (tax / pretax).dropna()
tax_avg = tax_hist.mean() if not tax_hist.empty else 0.20

tax_rate = st.sidebar.slider(
    "Tax Rate (%)",
    5.0, 35.0,
    float(round(tax_avg * 100, 1)),
    0.5
) / 100

st.sidebar.caption(f"Avg: {tax_avg:.1%}")


# Reinvestment (simplified realistic range)
reinvestment_rate = st.sidebar.slider(
    "Reinvestment Rate (%)",
    10.0, 60.0,
    35.0,
    0.5
) / 100

st.sidebar.caption("Typical corporate range")


# -----------------------------
# VALUATION ASSUMPTIONS
# -----------------------------
st.sidebar.subheader("Valuation Assumptions")

wacc = st.sidebar.slider("WACC (%)", 6.0, 14.0, 9.0, 0.5) / 100
terminal_growth = st.sidebar.slider("Terminal Growth (%)", 1.0, 4.0, 3.0, 0.25) / 100
years = st.sidebar.slider("Projection Years", 3, 10, 5)


# -----------------------------
# BALANCE SHEET (LOCKED)
# -----------------------------
st.sidebar.subheader("Balance Sheet")

st.sidebar.metric("Debt", f"${debt:,.0f}M")
st.sidebar.metric("Cash", f"${cash:,.0f}M")
st.sidebar.metric("Shares", f"{shares_outstanding:,.0f}M")


# -----------------------------
# DCF
# -----------------------------
revenues = []
fcfs = []
pv_fcfs = []

rev_val = starting_revenue

for t in range(1, years + 1):
    rev_val *= (1 + growth_rate)
    ebit_val = rev_val * ebit_margin
    nopat = ebit_val * (1 - tax_rate)
    reinvest = nopat * reinvestment_rate
    fcf = nopat - reinvest

    pv = fcf / ((1 + wacc) ** t)

    revenues.append(rev_val)
    fcfs.append(fcf)
    pv_fcfs.append(pv)

terminal_value = fcfs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
pv_terminal = terminal_value / ((1 + wacc) ** years)

enterprise_value = sum(pv_fcfs) + pv_terminal
equity_value = enterprise_value - debt + cash
intrinsic_value = equity_value / shares_outstanding

upside = (intrinsic_value - final_price) / final_price * 100


# -----------------------------
# OUTPUT
# -----------------------------
st.subheader(f"{ticker} Valuation")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Market Price", f"${final_price:,.2f}")
c2.metric("Intrinsic Value", f"${intrinsic_value:,.2f}")
c3.metric("Enterprise Value", f"${enterprise_value:,.0f}M")
c4.metric("Upside", f"{upside:.2f}%")

if intrinsic_value > final_price:
    st.success("Undervalued")
else:
    st.warning("Overvalued")


# -----------------------------
# CHART
# -----------------------------
df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Revenue": revenues,
    "FCF": fcfs
})

fig = px.line(df, x="Year", y="Revenue", title="Revenue Projection")
st.plotly_chart(fig, use_container_width=True)
