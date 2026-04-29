import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

st.set_page_config(
    page_title="TSM DCF Valuation App",
    page_icon="📈",
    layout="wide"
)

# -----------------------------
# Custom Styling
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%);
}
.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #0f172a;
}
.subtitle {
    font-size: 18px;
    color: #475569;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="main-title">📊 Equity Valuation App</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Estimate intrinsic value using a DCF model</div>', unsafe_allow_html=True)

st.write("")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("Valuation Inputs")

ticker = st.sidebar.text_input("Stock Ticker", value="TSM").upper()

starting_revenue = st.sidebar.number_input("Starting Revenue ($ millions)", value=90000.0)
growth_rate = st.sidebar.slider("Growth Rate (%)", 0.0, 30.0, 10.0) / 100
ebit_margin = st.sidebar.slider("EBIT Margin (%)", 0.0, 70.0, 45.0) / 100
tax_rate = st.sidebar.slider("Tax Rate (%)", 0.0, 40.0, 20.0) / 100
reinvestment_rate = st.sidebar.slider("Reinvestment Rate (%)", 0.0, 80.0, 35.0) / 100

wacc = st.sidebar.slider("WACC (%)", 1.0, 20.0, 9.0) / 100
terminal_growth = st.sidebar.slider("Terminal Growth (%)", 0.0, 6.0, 3.0) / 100
years = st.sidebar.slider("Projection Years", 3, 10, 5)

debt = st.sidebar.number_input("Debt ($ millions)", value=30000.0)
cash = st.sidebar.number_input("Cash ($ millions)", value=50000.0)
shares = st.sidebar.number_input("Shares Outstanding (millions)", value=5186.0)

# -----------------------------
# SAFE MARKET DATA (FIXED)
# -----------------------------
@st.cache_data(ttl=3600)
def get_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="5d")

        if not df.empty:
            return df["Close"].iloc[-1]
        return None
    except:
        return None

current_price = get_price(ticker)
company_name = ticker

# -----------------------------
# DCF CALCULATIONS
# -----------------------------
revenues = []
fcfs = []
pv_fcfs = []

rev = starting_revenue

for t in range(1, years + 1):
    rev *= (1 + growth_rate)
    ebit = rev * ebit_margin
    nopat = ebit * (1 - tax_rate)
    reinvestment = nopat * reinvestment_rate
    fcf = nopat - reinvestment
    pv = fcf / ((1 + wacc) ** t)

    revenues.append(rev)
    fcfs.append(fcf)
    pv_fcfs.append(pv)

terminal_value = fcfs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
pv_terminal = terminal_value / ((1 + wacc) ** years)

enterprise_value = sum(pv_fcfs) + pv_terminal
equity_value = enterprise_value - debt + cash
value_per_share = equity_value / shares

if current_price:
    diff = (value_per_share - current_price) / current_price * 100
else:
    diff = None

# -----------------------------
# OUTPUT
# -----------------------------
st.subheader(f"{company_name} ({ticker}) Valuation")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Market Price", f"${current_price:,.2f}" if current_price else "N/A")
c2.metric("Intrinsic Value", f"${value_per_share:,.2f}")
c3.metric("Enterprise Value", f"${enterprise_value:,.0f}M")
c4.metric("Upside/Downside", f"{diff:,.2f}%" if diff else "N/A")

if diff:
    if value_per_share > current_price:
        st.success("Stock appears undervalued")
    else:
        st.warning("Stock appears overvalued")

# -----------------------------
# TABLE
# -----------------------------
df = pd.DataFrame({
    "Year": np.arange(1, years + 1),
    "Revenue": revenues,
    "FCF": fcfs,
    "PV of FCF": pv_fcfs
})

st.subheader("DCF Projection")
st.dataframe(df)

# -----------------------------
# CHARTS
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("Revenue Growth")
    fig1 = px.line(df, x="Year", y="Revenue", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Free Cash Flow")
    fig2 = px.bar(df, x="Year", y="FCF")
    st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# EXPLANATION
# -----------------------------
st.subheader("How It Works")

with st.expander("DCF Logic"):
    st.write("""
    1. Revenue grows each year
    2. EBIT margin applied
    3. Taxes deducted → NOPAT
    4. Reinvestment removed → Free Cash Flow
    5. Discounted using WACC
    6. Terminal value added
    """)

st.caption("Built for FINA 4011")
