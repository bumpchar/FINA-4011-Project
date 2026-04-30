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
st.write("Estimate a stock’s intrinsic value using Yahoo Finance fundamentals and realistic user assumptions.")

st.sidebar.header("Valuation Inputs")

ticker = st.sidebar.text_input("Stock Ticker", value="TSM").upper()


# -----------------------------
# Yahoo Finance Data Pulls
# -----------------------------
@st.cache_data(ttl=3600)
def get_yahoo_data(stock_ticker):
    try:
        stock = yf.Ticker(stock_ticker)

        price_data = stock.history(period="1mo")
        current_price = None
        if price_data is not None and not price_data.empty:
            current_price = float(price_data["Close"].dropna().iloc[-1])

        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        info = stock.info

        return current_price, income_stmt, balance_sheet, info

    except Exception:
        return None, pd.DataFrame(), pd.DataFrame(), {}


def get_statement_value(statement, possible_labels):
    try:
        for label in possible_labels:
            if label in statement.index:
                values = statement.loc[label].dropna()
                if not values.empty:
                    return float(values.iloc[0]) / 1_000_000
        return None
    except Exception:
        return None


def get_historical_values(statement, possible_labels):
    try:
        for label in possible_labels:
            if label in statement.index:
                values = statement.loc[label].dropna()
                if not values.empty:
                    return values.astype(float) / 1_000_000
        return pd.Series(dtype=float)
    except Exception:
        return pd.Series(dtype=float)


def safe_slider_range(values, default_min, default_max, padding=0.05):
    values = pd.Series(values).dropna()

    if values.empty:
        return default_min, default_max

    low = max(0.0, float(values.min()) - padding)
    high = float(values.max()) + padding

    if low >= high:
        low = default_min
        high = default_max

    return round(low * 100, 1), round(high * 100, 1)


current_price, income_stmt, balance_sheet, info = get_yahoo_data(ticker)


# -----------------------------
# Market Price
# -----------------------------
st.sidebar.subheader("Market Price")

use_manual_price = st.sidebar.checkbox(
    "Use manual market price",
    value=True if current_price is None else False
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
    st.sidebar.warning("Live market price could not load. Manual price is being used.")
else:
    st.sidebar.success(f"Live price loaded: ${current_price:,.2f}")


# -----------------------------
# Locked Yahoo Finance Inputs
# -----------------------------
starting_revenue = get_statement_value(
    income_stmt,
    ["Total Revenue", "Revenue"]
)

total_debt = get_statement_value(
    balance_sheet,
    ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Long Term Debt"]
)

cash = get_statement_value(
    balance_sheet,
    ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]
)

shares_outstanding = None
try:
    if info.get("sharesOutstanding") is not None:
        shares_outstanding = float(info.get("sharesOutstanding")) / 1_000_000
except Exception:
    shares_outstanding = None


if starting_revenue is None:
    starting_revenue = 90000.0

if total_debt is None:
    total_debt = 30000.0

if cash is None:
    cash = 50000.0

if shares_outstanding is None or shares_outstanding <= 0:
    shares_outstanding = 5186.0


st.sidebar.subheader("Operating Assumptions")

st.sidebar.metric(
    "Starting Revenue",
    f"${starting_revenue:,.0f}M"
)
st.sidebar.caption("Pulled directly from Yahoo Finance and locked for the user.")


# -----------------------------
# Historical Assumption Calculations
# -----------------------------
historical_revenue = get_historical_values(
    income_stmt,
    ["Total Revenue", "Revenue"]
)

historical_ebit = get_historical_values(
    income_stmt,
    ["EBIT", "Operating Income"]
)

historical_tax_expense = get_historical_values(
    income_stmt,
    ["Tax Provision", "Income Tax Expense"]
)

historical_pretax_income = get_historical_values(
    income_stmt,
    ["Pretax Income", "Income Before Tax"]
)

historical_net_income = get_historical_values(
    income_stmt,
    ["Net Income", "Net Income Common Stockholders"]
)

historical_capex = get_historical_values(
    income_stmt,
    ["Capital Expenditure", "Capital Expenditures"]
)


# Revenue growth from historical revenue
revenue_growth_rates = historical_revenue.sort_index().pct_change().dropna()
growth_min, growth_max = safe_slider_range(revenue_growth_rates, 0.0, 0.30, padding=0.03)
growth_avg = revenue_growth_rates.mean() if not revenue_growth_rates.empty else 0.10

growth_rate = st.sidebar.slider(
    "Annual Revenue Growth Rate (%)",
    min_value=float(growth_min),
    max_value=float(growth_max),
    value=float(round(growth_avg * 100, 1)) if growth_min <= round(growth_avg * 100, 1) <= growth_max else 10.0,
    step=0.5
) / 100

st.sidebar.caption(
    f"Historical average: {growth_avg:.1%}. Range based on recent Yahoo Finance revenue trends."
)


# EBIT margin
if not historical_revenue.empty and not historical_ebit.empty:
    common_dates = historical_revenue.index.intersection(historical_ebit.index)
    ebit_margins = historical_ebit.loc[common_dates] / historical_revenue.loc[common_dates]
else:
    ebit_margins = pd.Series(dtype=float)

ebit_min, ebit_max = safe_slider_range(ebit_margins, 0.20, 0.60, padding=0.03)
ebit_avg = ebit_margins.mean() if not ebit_margins.empty else 0.45

ebit_margin = st.sidebar.slider(
    "EBIT Margin (%)",
    min_value=float(ebit_min),
    max_value=float(ebit_max),
    value=float(round(ebit_avg * 100, 1)) if ebit_min <= round(ebit_avg * 100, 1) <= ebit_max else 45.0,
    step=0.5
) / 100

st.sidebar.caption(
    f"Historical average: {ebit_avg:.1%}. This keeps the margin assumption close to the company’s actual past performance."
)


# Tax rate
if not historical_tax_expense.empty and not historical_pretax_income.empty:
    common_dates = historical_tax_expense.index.intersection(historical_pretax_income.index)
    tax_rates = historical_tax_expense.loc[common_dates] / historical_pretax_income.loc[common_dates]
    tax_rates = tax_rates[(tax_rates >= 0) & (tax_rates <= 0.50)]
else:
    tax_rates = pd.Series(dtype=float)

tax_min, tax_max = safe_slider_range(tax_rates, 0.05, 0.35, padding=0.03)
tax_avg = tax_rates.mean() if not tax_rates.empty else 0.20

tax_rate = st.sidebar.slider(
    "Tax Rate (%)",
    min_value=float(tax_min),
    max_value=float(tax_max),
    value=float(round(tax_avg * 100, 1)) if tax_min <= round(tax_avg * 100, 1) <= tax_max else 20.0,
    step=0.5
) / 100

st.sidebar.caption(
    f"Historical average: {tax_avg:.1%}. Based on tax expense divided by pre-tax income."
)


# Reinvestment rate
# If direct CapEx does not load from Yahoo Finance income statement, use a reasonable fallback.
if not historical_capex.empty and not historical_net_income.empty:
    common_dates = historical_capex.index.intersection(historical_net_income.index)
    reinvestment_rates = abs(historical_capex.loc[common_dates]) / historical_net_income.loc[common_dates]
    reinvestment_rates = reinvestment_rates[(reinvestment_rates >= 0) & (reinvestment_rates <= 1.00)]
else:
    reinvestment_rates = pd.Series(dtype=float)

reinv_min, reinv_max = safe_slider_range(reinvestment_rates, 0.10, 0.70, padding=0.05)
reinv_avg = reinvestment_rates.mean() if not reinvestment_rates.empty else 0.35

reinvestment_rate = st.sidebar.slider(
    "Reinvestment Rate (%)",
    min_value=float(reinv_min),
    max_value=float(reinv_max),
    value=float(round(reinv_avg * 100, 1)) if reinv_min <= round(reinv_avg * 100, 1) <= reinv_max else 35.0,
    step=0.5
) / 100

st.sidebar.caption(
    f"Historical average: {reinv_avg:.1%}. Estimated from capital spending relative to income when available."
)


# -----------------------------
# Valuation Assumptions
# -----------------------------
st.sidebar.subheader("Valuation Assumptions")

wacc = st.sidebar.slider(
    "WACC / Discount Rate (%)",
    min_value=6.0,
    max_value=14.0,
    value=9.0,
    step=0.5
) / 100

st.sidebar.caption("Realistic DCF range for a large public company is usually around mid-single digits to low teens.")

terminal_growth = st.sidebar.slider(
    "Terminal Growth Rate (%)",
    min_value=1.0,
    max_value=4.0,
    value=3.0,
    step=0.25
) / 100

st.sidebar.caption("Terminal growth is capped because long-run growth should not exceed the economy forever.")

projection_years = st.sidebar.slider(
    "Projection Years",
    min_value=3,
    max_value=10,
    value=5
)


# -----------------------------
# Locked Balance Sheet Assumptions
# -----------------------------
st.sidebar.subheader("Balance Sheet Assumptions")

st.sidebar.metric(
    "Total Debt",
    f"${total_debt:,.0f}M"
)

st.sidebar.metric(
    "Cash & Equivalents",
    f"${cash:,.0f}M"
)

st.sidebar.metric(
    "Shares Outstanding",
    f"{shares_outstanding:,.0f}M"
)

st.sidebar.caption("Balance sheet assumptions are pulled from Yahoo Finance and locked for the user.")


# -----------------------------
# Error Checks
# -----------------------------
if wacc <= terminal_growth:
    st.error("WACC must be greater than the terminal growth rate.")
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
equity_value = enterprise_value - total_debt + cash
intrinsic_value_per_share = equity_value / shares_outstanding

upside_downside = ((intrinsic_value_per_share - final_price) / final_price) * 100


# -----------------------------
# Output Summary
# -----------------------------
st.subheader(f"{ticker} Valuation Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Current Market Price", f"${final_price:,.2f}")
col2.metric("Intrinsic Value", f"${intrinsic_value_per_share:,.2f}")
col3.metric("Enterprise Value", f"${enterprise_value:,.0f}M")
col4.metric("Upside / Downside", f"{upside_downside:,.2f}%")

if intrinsic_value_per_share > final_price:
    st.success("Based on your assumptions, the stock appears undervalued.")
elif intrinsic_value_per_share < final_price:
    st.warning("Based on your assumptions, the stock appears overvalued.")
else:
    st.info("Based on your assumptions, the stock appears fairly valued.")


# -----------------------------
# Locked Input Display
# -----------------------------
st.subheader("Yahoo Finance Inputs Used in the Model")

locked_inputs = pd.DataFrame({
    "Input": [
        "Starting Revenue",
        "Total Debt",
        "Cash & Equivalents",
        "Shares Outstanding"
    ],
    "Value": [
        f"${starting_revenue:,.0f}M",
        f"${total_debt:,.0f}M",
        f"${cash:,.0f}M",
        f"{shares_outstanding:,.0f}M"
    ],
    "User Editable?": [
        "No",
        "No",
        "No",
        "No"
    ]
})

st.dataframe(locked_inputs, use_container_width=True)


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
}), use_container_width=True)


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
        total_debt,
        cash,
        equity_value,
        shares_outstanding,
        intrinsic_value_per_share
    ]
})

st.dataframe(breakdown.style.format({"Value": "{:,.2f}"}), use_container_width=True)


# -----------------------------
# Explanation
# -----------------------------
st.subheader("Quick Explanation")

with st.expander("What changed on this page?"):
    st.write("""
    Starting revenue, total debt, cash and equivalents, and shares outstanding are pulled from Yahoo Finance.
    These values are locked so the user cannot manually change the company's actual financial starting point.
    """)

with st.expander("Why are the sliders more realistic now?"):
    st.write("""
    The adjustable assumptions use historical Yahoo Finance data when available.
    This helps keep the DCF model grounded in the company's past performance instead of allowing unrealistic assumptions.
    """)

with st.expander("What is this page calculating?"):
    st.write("""
    This page estimates company value by projecting free cash flow, discounting it back to today using WACC,
    calculating terminal value, and then adjusting enterprise value for debt, cash, and shares outstanding.
    """)

st.caption("All values are estimates and depend on Yahoo Finance data availability and user-selected assumptions.")
