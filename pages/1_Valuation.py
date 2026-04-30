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
.formula-card {
    background-color: white;
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 14px;
}
.formula-box {
    background-color: #f1f5f9;
    padding: 10px;
    border-radius: 10px;
    font-family: monospace;
    color: #0f172a;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 DCF Valuation Model")
st.write("Estimate a stock’s intrinsic value and compare it to the current market price.")

st.sidebar.header("Valuation Inputs")
ticker = st.sidebar.text_input("Stock Ticker", value="TSM").upper()


# -----------------------------
# Yahoo Finance Pulls
# -----------------------------
@st.cache_data(ttl=300)
def get_market_price(stock_ticker):
    try:
        stock = yf.Ticker(stock_ticker)

        try:
            price = stock.fast_info.get("last_price", None)
            if price is not None:
                return float(price)
        except Exception:
            pass

        price_data = stock.history(period="5d")
        if price_data is not None and not price_data.empty:
            return float(price_data["Close"].dropna().iloc[-1])

        return None
    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_yahoo_data(stock_ticker):
    try:
        stock = yf.Ticker(stock_ticker)
        return stock.financials, stock.balance_sheet, stock.cashflow, stock.info
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}


def get_statement_value(statement, labels, fallback):
    try:
        for label in labels:
            if label in statement.index:
                values = statement.loc[label].dropna()
                if not values.empty:
                    return float(values.iloc[0]) / 1_000_000
    except Exception:
        pass
    return fallback


def get_statement_series(statement, labels):
    try:
        for label in labels:
            if label in statement.index:
                values = statement.loc[label].dropna()
                if not values.empty:
                    return values.astype(float) / 1_000_000
    except Exception:
        pass
    return pd.Series(dtype=float)


def slider_bounds(series, fallback_min, fallback_max, padding=0.03):
    series = pd.Series(series).replace([np.inf, -np.inf], np.nan).dropna()

    if series.empty:
        return fallback_min, fallback_max

    low = max(0.0, float(series.min()) - padding)
    high = float(series.max()) + padding

    if low >= high:
        return fallback_min, fallback_max

    return round(low * 100, 1), round(high * 100, 1)


current_price = get_market_price(ticker)
income_stmt, balance_sheet, cashflow, info = get_yahoo_data(ticker)


# -----------------------------
# Market Price
# -----------------------------
st.sidebar.subheader("Market Price")

use_manual_price = st.sidebar.checkbox(
    "Use manual market price",
    value=False if current_price is not None else True
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
    st.sidebar.error("Live market price could not load. Manual price is being used.")
else:
    st.sidebar.success(f"Live price loaded: ${current_price:,.2f}")


# -----------------------------
# Locked Yahoo Finance Inputs
# -----------------------------
starting_revenue = get_statement_value(
    income_stmt,
    ["Total Revenue", "Revenue"],
    90000.0
)

debt = get_statement_value(
    balance_sheet,
    ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Long Term Debt"],
    30000.0
)

cash = get_statement_value(
    balance_sheet,
    ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
    50000.0
)

try:
    shares_outstanding = float(info.get("sharesOutstanding")) / 1_000_000
except Exception:
    shares_outstanding = 5186.0

 if shares_outstanding <= 0:
    shares_outstanding = 5186.0


# -----------------------------
# Operating Assumptions
# -----------------------------
st.sidebar.subheader("Operating Assumptions")

st.sidebar.metric("Starting Revenue", f"${starting_revenue:,.0f}M")
st.sidebar.caption("Pulled from Yahoo Finance and locked.")

historical_revenue = get_statement_series(income_stmt, ["Total Revenue", "Revenue"])
historical_ebit = get_statement_series(income_stmt, ["EBIT", "Operating Income"])
historical_tax = get_statement_series(income_stmt, ["Tax Provision", "Income Tax Expense"])
historical_pretax = get_statement_series(income_stmt, ["Pretax Income", "Income Before Tax"])
historical_capex = get_statement_series(cashflow, ["Capital Expenditure", "Capital Expenditures"])
historical_net_income = get_statement_series(income_stmt, ["Net Income", "Net Income Common Stockholders"])


# Revenue Growth
revenue_growth_rates = historical_revenue.sort_index().pct_change().dropna()
growth_avg = revenue_growth_rates.mean() if not revenue_growth_rates.empty else 0.10
growth_min, growth_max = slider_bounds(revenue_growth_rates, 0.0, 0.30, padding=0.03)
growth_default = round(growth_avg * 100, 1)
growth_default = min(max(growth_default, growth_min), growth_max)

growth_rate = st.sidebar.slider(
    "Annual Revenue Growth Rate (%)",
    min_value=float(growth_min),
    max_value=float(growth_max),
    value=float(growth_default),
    step=0.5
) / 100

st.sidebar.caption(f"Recent historical average: {growth_avg:.1%}")


# EBIT Margin
if not historical_revenue.empty and not historical_ebit.empty:
    common_dates = historical_revenue.index.intersection(historical_ebit.index)
    ebit_margins = historical_ebit.loc[common_dates] / historical_revenue.loc[common_dates]
else:
    ebit_margins = pd.Series(dtype=float)

ebit_avg = ebit_margins.mean() if not ebit_margins.empty else 0.45
ebit_min, ebit_max = slider_bounds(ebit_margins, 0.20, 0.60, padding=0.03)
ebit_default = round(ebit_avg * 100, 1)
ebit_default = min(max(ebit_default, ebit_min), ebit_max)

ebit_margin = st.sidebar.slider(
    "EBIT Margin (%)",
    min_value=float(ebit_min),
    max_value=float(ebit_max),
    value=float(ebit_default),
    step=0.5
) / 100

st.sidebar.caption(f"Recent historical average: {ebit_avg:.1%}")


# Tax Rate
if not historical_tax.empty and not historical_pretax.empty:
    common_dates = historical_tax.index.intersection(historical_pretax.index)
    tax_rates = historical_tax.loc[common_dates] / historical_pretax.loc[common_dates]
    tax_rates = tax_rates[(tax_rates >= 0) & (tax_rates <= 0.50)]
else:
    tax_rates = pd.Series(dtype=float)

tax_avg = tax_rates.mean() if not tax_rates.empty else 0.20
tax_min, tax_max = slider_bounds(tax_rates, 0.05, 0.35, padding=0.03)
tax_default = round(tax_avg * 100, 1)
tax_default = min(max(tax_default, tax_min), tax_max)

tax_rate = st.sidebar.slider(
    "Tax Rate (%)",
    min_value=float(tax_min),
    max_value=float(tax_max),
    value=float(tax_default),
    step=0.5
) / 100

st.sidebar.caption(f"Recent historical average: {tax_avg:.1%}")


# Reinvestment Rate
if not historical_capex.empty and not historical_net_income.empty:
    common_dates = historical_capex.index.intersection(historical_net_income.index)
    reinvestment_rates = abs(historical_capex.loc[common_dates]) / historical_net_income.loc[common_dates]
    reinvestment_rates = reinvestment_rates[(reinvestment_rates >= 0) & (reinvestment_rates <= 1.00)]
else:
    reinvestment_rates = pd.Series(dtype=float)

reinv_avg = reinvestment_rates.mean() if not reinvestment_rates.empty else 0.35
reinv_min, reinv_max = slider_bounds(reinvestment_rates, 0.10, 0.70, padding=0.05)
reinv_default = round(reinv_avg * 100, 1)
reinv_default = min(max(reinv_default, reinv_min), reinv_max)

reinvestment_rate = st.sidebar.slider(
    "Reinvestment Rate (%)",
    min_value=float(reinv_min),
    max_value=float(reinv_max),
    value=float(reinv_default),
    step=0.5
) / 100

st.sidebar.caption(f"Recent historical average: {reinv_avg:.1%}")


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

terminal_growth = st.sidebar.slider(
    "Terminal Growth Rate (%)",
    min_value=1.0,
    max_value=4.0,
    value=3.0,
    step=0.25
) / 100

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

st.sidebar.metric("Total Debt", f"${debt:,.0f}M")
st.sidebar.metric("Cash & Equivalents", f"${cash:,.0f}M")
st.sidebar.metric("Shares Outstanding", f"{shares_outstanding:,.0f}M")
st.sidebar.caption("Pulled from Yahoo Finance and locked.")


# -----------------------------
# Safety Checks
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
equity_value = enterprise_value - debt + cash
intrinsic_value_per_share = equity_value / shares_outstanding

upside_downside = ((intrinsic_value_per_share - final_price) / final_price) * 100


# -----------------------------
# Valuation Summary
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
# Yahoo Finance Inputs Table
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
        f"${debt:,.0f}M",
        f"${cash:,.0f}M",
        f"{shares_outstanding:,.0f}M"
    ],
    "User Editable?": ["No", "No", "No", "No"]
})

st.dataframe(locked_inputs, use_container_width=True)


# -----------------------------
# DCF Projection Table
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
# Visuals
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

st.dataframe(breakdown.style.format({"Value": "{:,.2f}"}), use_container_width=True)


# -----------------------------
# Formula Breakdown
# -----------------------------
st.subheader("Formula Breakdown Using Selected Inputs")

first_year_revenue = revenues[0]
first_year_ebit = ebit_values[0]
first_year_nopat = nopat_values[0]
first_year_reinvestment = reinvestment_values[0]
first_year_fcf = fcf_values[0]
first_year_pv_fcf = pv_fcf_values[0]
final_year_fcf = fcf_values[-1]

formula_df = pd.DataFrame({
    "Step": [
        "1. Revenue Projection",
        "2. EBIT",
        "3. NOPAT",
        "4. Reinvestment",
        "5. Free Cash Flow",
        "6. Present Value of FCF",
        "7. Terminal Value",
        "8. Enterprise Value",
        "9. Equity Value",
        "10. Intrinsic Value Per Share"
    ],
    "Formula": [
        "Revenue next year = Revenue this year × (1 + Growth Rate)",
        "EBIT = Revenue × EBIT Margin",
        "NOPAT = EBIT × (1 − Tax Rate)",
        "Reinvestment = NOPAT × Reinvestment Rate",
        "Free Cash Flow = NOPAT − Reinvestment",
        "PV of FCF = FCF ÷ (1 + WACC)^Year",
        "Terminal Value = Final Year FCF × (1 + Terminal Growth) ÷ (WACC − Terminal Growth)",
        "Enterprise Value = PV of Projected FCF + PV of Terminal Value",
        "Equity Value = Enterprise Value − Debt + Cash",
        "Intrinsic Value Per Share = Equity Value ÷ Shares Outstanding"
    ],
    "Calculation Using Current Inputs": [
        f"${starting_revenue:,.2f}M × (1 + {growth_rate:.2%}) = ${first_year_revenue:,.2f}M",
        f"${first_year_revenue:,.2f}M × {ebit_margin:.2%} = ${first_year_ebit:,.2f}M",
        f"${first_year_ebit:,.2f}M × (1 − {tax_rate:.2%}) = ${first_year_nopat:,.2f}M",
        f"${first_year_nopat:,.2f}M × {reinvestment_rate:.2%} = ${first_year_reinvestment:,.2f}M",
        f"${first_year_nopat:,.2f}M − ${first_year_reinvestment:,.2f}M = ${first_year_fcf:,.2f}M",
        f"${first_year_fcf:,.2f}M ÷ (1 + {wacc:.2%})^1 = ${first_year_pv_fcf:,.2f}M",
        f"${final_year_fcf:,.2f}M × (1 + {terminal_growth:.2%}) ÷ ({wacc:.2%} − {terminal_growth:.2%}) = ${terminal_value:,.2f}M",
        f"${sum(pv_fcf_values):,.2f}M + ${pv_terminal_value:,.2f}M = ${enterprise_value:,.2f}M",
        f"${enterprise_value:,.2f}M − ${debt:,.2f}M + ${cash:,.2f}M = ${equity_value:,.2f}M",
        f"${equity_value:,.2f}M ÷ {shares_outstanding:,.2f}M shares = ${intrinsic_value_per_share:,.2f}"
    ]
})

st.dataframe(formula_df, use_container_width=True)

with st.expander("How to read this formula breakdown"):
    st.write("""
    This section connects the model formulas directly to the selected inputs.
    For example, EBIT is calculated by multiplying projected revenue by the selected EBIT margin.
    As the user changes growth rate, EBIT margin, tax rate, reinvestment rate, WACC, or terminal growth,
    the formula calculations update automatically.
    """)


# -----------------------------
# Quick Explanation
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

with st.expander("Why do assumptions matter?"):
    st.write("""
    Small changes in growth rate, WACC, terminal growth, and margins can create large changes in the final valuation.
    This is why DCF models are useful, but also sensitive to assumptions.
    """)

st.caption("All values are estimates and depend on Yahoo Finance data availability and user-selected assumptions.")
