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

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%);
}
.card {
    background-color: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 18px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.title("📈 DCF Valuation Model")
st.write("Estimate a stock’s intrinsic value and compare it to the current market price.")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("Valuation Inputs")

ticker = st.sidebar.text_input("Stock Ticker", value="TSM").upper()

st.sidebar.subheader("Operating Assumptions")

starting_revenue = st.sidebar.number_input(
    "Starting Revenue ($ millions)",
    value=90000.0,
    step=1000.0
)

growth_rate = st.sidebar.slider(
    "Annual Revenue Growth Rate (%)",
    min_value=0.0,
    max_value=30.0,
    value=10.0,
    step=0.5
) / 100

ebit_margin = st.sidebar.slider(
    "EBIT Margin (%)",
    min_value=0.0,
    max_value=70.0,
    value=45.0,
    step=0.5
) / 100

tax_rate = st.sidebar.slider(
    "Tax Rate (%)",
    min_value=0.0,
    max_value=40.0,
    value=20.0,
    step=0.5
) / 100

reinvestment_rate = st.sidebar.slider(
    "Reinvestment Rate (%)",
    min_value=0.0,
    max_value=80.0,
    value=35.0,
    step=0.5
) / 100

st.sidebar.subheader("Valuation Assumptions")

wacc = st.sidebar.slider(
    "WACC / Discount Rate (%)",
    min_value=1.0,
    max_value=20.0,
    value=9.0,
    step=0.5
) / 100

terminal_growth = st.sidebar.slider(
    "Terminal Growth Rate (%)",
    min_value=0.0,
    max_value=6.0,
    value=3.0,
    step=0.25
) / 100

projection_years = st.sidebar.slider(
    "Projection Years",
    min_value=3,
    max_value=10,
    value=5
)

st.sidebar.subheader("Balance Sheet Assumptions")

debt = st.sidebar.number_input(
    "Total Debt ($ millions)",
    value=30000.0,
    step=1000.0
)

cash = st.sidebar.number_input(
    "Cash & Equivalents ($ millions)",
    value=50000.0,
    step=1000.0
)

shares_outstanding = st.sidebar.number_input(
    "Shares Outstanding (millions)",
    value=5186.0,
    step=10.0
)

# -----------------------------
# Market Price Function
# -----------------------------
@st.cache_data(ttl=3600)
def get_market_price(stock_ticker):
    try:
        stock = yf.Ticker(stock_ticker)
        price_data = stock.history(period="5d")

        if not price_data.empty:
            return float(price_data["Close"].iloc[-1])
        return None
    except Exception:
        return None

current_price = get_market_price(ticker)

# -----------------------------
# Validation
# -----------------------------
if wacc <= terminal_growth:
    st.error("WACC must be greater than the terminal growth rate for the terminal value formula to work.")
    st.stop()

if shares_outstanding <= 0:
    st.error("Shares outstanding must be greater than zero.")
    st.stop()

# -----------------------------
# DCF Calculations
# -----------------------------
revenues = []
ebit_values = []
nopat_values = []
reinvestment_values = []
fcf_values = []
pv_fcf_values = []

revenue = starting_revenue

for year in range(1, projection_years + 1):
    revenue = revenue * (1 + growth_rate)
    ebit = revenue * ebit_margin
    nopat = ebit * (1 - tax_rate)
    reinvestment = nopat * reinvestment_rate
    fcf = nopat - reinvestment
    pv_fcf = fcf / ((1 + wacc) ** year)

    revenues.append(revenue)
    ebit_values.append(ebit)
    nopat_values.append(nopat)
    reinvestment_values.append(reinvestment)
    fcf_values.append(fcf)
    pv_fcf_values.append(pv_fcf)

terminal_value = fcf_values[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
pv_terminal_value = terminal_value / ((1 + wacc) ** projection_years)

enterprise_value = sum(pv_fcf_values) + pv_terminal_value
equity_value = enterprise_value - debt + cash
intrinsic_value_per_share = equity_value / shares_outstanding

upside_downside = None
if current_price is not None and current_price > 0:
    upside_downside = ((intrinsic_value_per_share - current_price) / current_price) * 100

# -----------------------------
# Summary Metrics
# -----------------------------
st.subheader(f"{ticker} Valuation Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Current Market Price",
    f"${current_price:,.2f}" if current_price is not None else "Unavailable"
)

col2.metric(
    "Intrinsic Value",
    f"${intrinsic_value_per_share:,.2f}"
)

col3.metric(
    "Enterprise Value",
    f"${enterprise_value:,.0f}M"
)

col4.metric(
    "Upside / Downside",
    f"{upside_downside:,.2f}%" if upside_downside is not None else "Unavailable"
)

if upside_downside is not None:
    if intrinsic_value_per_share > current_price:
        st.success("Based on your assumptions, the stock appears undervalued.")
    elif intrinsic_value_per_share < current_price:
        st.warning("Based on your assumptions, the stock appears overvalued.")
    else:
        st.info("Based on your assumptions, the stock appears fairly valued.")
else:
    st.info("Market price could not be loaded, but the DCF valuation still works.")

# -----------------------------
# Projection Table
# -----------------------------
df = pd.DataFrame({
    "Year": np.arange(1, projection_years + 1),
    "Revenue": revenues,
    "EBIT": ebit_values,
    "NOPAT": nopat_values,
    "Reinvestment": reinvestment_values,
    "Free Cash Flow": fcf_values,
    "PV of FCF": pv_fcf_values
})

st.subheader("Step-by-Step DCF Projection")

st.dataframe(df.style.format({
    "Revenue": "${:,.2f}M",
    "EBIT": "${:,.2f}M",
    "NOPAT": "${:,.2f}M",
    "Reinvestment": "${:,.2f}M",
    "Free Cash Flow": "${:,.2f}M",
    "PV of FCF": "${:,.2f}M"
}))

# -----------------------------
# Charts
# -----------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Projected Revenue")
    fig_revenue = px.line(
        df,
        x="Year",
        y="Revenue",
        markers=True,
        title="Revenue Projection"
    )
    st.plotly_chart(fig_revenue, use_container_width=True)

with chart_col2:
    st.subheader("Projected Free Cash Flow")
    fig_fcf = px.bar(
        df,
        x="Year",
        y="Free Cash Flow",
        title="Free Cash Flow Projection"
    )
    st.plotly_chart(fig_fcf, use_container_width=True)

# -----------------------------
# Valuation Breakdown
# -----------------------------
st.subheader("Valuation Breakdown")

breakdown = pd.DataFrame({
    "Component": [
        "PV of Projected Free Cash Flows",
        "PV of Terminal Value",
        "Enterprise Value",
        "Less: Debt",
        "Add: Cash",
        "Equity Value",
        "Shares Outstanding",
        "Intrinsic Value Per Share"
    ],
    "Value": [
        sum(pv_fcf_values),
        pv_terminal_value,
        enterprise_value,
        debt,
        cash,
        equity_value,
        shares_outstanding,
        intrinsic_value_per_share
    ]
})

st.dataframe(breakdown.style.format({"Value": "{:,.2f}"}))

# -----------------------------
# Quick Explanation
# -----------------------------
st.subheader("Quick Explanation")

with st.expander("What is this page calculating?"):
    st.write("""
    This page estimates the value of a company based on the cash flows it is expected to generate in the future.
    The projected cash flows are discounted back to today using WACC, then adjusted for debt, cash, and shares outstanding.
    """)

with st.expander("Why do assumptions matter?"):
    st.write("""
    Small changes in growth rate, WACC, terminal growth, and margins can create large changes in the final valuation.
    This is why DCF models are useful, but also sensitive to assumptions.
    """)

st.caption("All values are estimates and depend on user inputs.")
