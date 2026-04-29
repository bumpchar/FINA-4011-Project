import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Sensitivity Analysis",
    page_icon="🔥",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%);
}
</style>
""", unsafe_allow_html=True)

st.title("🔥 Sensitivity Analysis")
st.write("See how the estimated intrinsic value changes when key DCF assumptions change.")

st.sidebar.header("Base Assumptions")

starting_revenue = st.sidebar.number_input(
    "Starting Revenue ($ millions)",
    value=90000.0,
    step=1000.0
)

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

projection_years = st.sidebar.slider(
    "Projection Years",
    min_value=3,
    max_value=10,
    value=5
)

terminal_growth = st.sidebar.slider(
    "Terminal Growth Rate (%)",
    min_value=0.0,
    max_value=6.0,
    value=3.0,
    step=0.25
) / 100

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

st.sidebar.header("Sensitivity Ranges")

growth_min = st.sidebar.slider(
    "Minimum Revenue Growth (%)",
    min_value=0.0,
    max_value=25.0,
    value=6.0,
    step=0.5
) / 100

growth_max = st.sidebar.slider(
    "Maximum Revenue Growth (%)",
    min_value=0.0,
    max_value=30.0,
    value=14.0,
    step=0.5
) / 100

wacc_min = st.sidebar.slider(
    "Minimum WACC (%)",
    min_value=1.0,
    max_value=20.0,
    value=7.0,
    step=0.5
) / 100

wacc_max = st.sidebar.slider(
    "Maximum WACC (%)",
    min_value=1.0,
    max_value=25.0,
    value=11.0,
    step=0.5
) / 100

if growth_min >= growth_max:
    st.error("Minimum revenue growth must be less than maximum revenue growth.")
    st.stop()

if wacc_min >= wacc_max:
    st.error("Minimum WACC must be less than maximum WACC.")
    st.stop()

if wacc_min <= terminal_growth:
    st.error("Minimum WACC must be greater than terminal growth rate.")
    st.stop()

if shares_outstanding <= 0:
    st.error("Shares outstanding must be greater than zero.")
    st.stop()

growth_rates = np.linspace(growth_min, growth_max, 5)
wacc_rates = np.linspace(wacc_min, wacc_max, 5)

def calculate_dcf_value(growth_rate, wacc):
    revenue = starting_revenue
    pv_fcfs = []
    final_fcf = 0

    for year in range(1, projection_years + 1):
        revenue = revenue * (1 + growth_rate)
        ebit = revenue * ebit_margin
        nopat = ebit * (1 - tax_rate)
        reinvestment = nopat * reinvestment_rate
        fcf = nopat - reinvestment
        pv_fcf = fcf / ((1 + wacc) ** year)

        pv_fcfs.append(pv_fcf)
        final_fcf = fcf

    terminal_value = final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_terminal_value = terminal_value / ((1 + wacc) ** projection_years)

    enterprise_value = sum(pv_fcfs) + pv_terminal_value
    equity_value = enterprise_value - debt + cash
    intrinsic_value = equity_value / shares_outstanding

    return intrinsic_value

sensitivity_rows = []

for wacc in wacc_rates:
    row = {"WACC": f"{wacc:.1%}"}
    for growth in growth_rates:
        row[f"{growth:.1%} Growth"] = calculate_dcf_value(growth, wacc)
    sensitivity_rows.append(row)

sensitivity_df = pd.DataFrame(sensitivity_rows)

st.subheader("Intrinsic Value Per Share Sensitivity Table")
st.write("This table shows estimated value per share under different revenue growth and WACC assumptions.")

format_dict = {
    col: "${:,.2f}" for col in sensitivity_df.columns if col != "WACC"
}

st.dataframe(sensitivity_df.style.format(format_dict), use_container_width=True)

heatmap_df = sensitivity_df.set_index("WACC")
heatmap_df = heatmap_df.astype(float)

st.subheader("Sensitivity Heatmap")

fig = px.imshow(
    heatmap_df,
    text_auto=".2f",
    title="Estimated Intrinsic Value Per Share",
    labels=dict(
        x="Revenue Growth Rate",
        y="WACC",
        color="Value Per Share"
    )
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("What This Shows")

col1, col2 = st.columns(2)

with col1:
    st.info("""
    Higher revenue growth generally increases the estimated intrinsic value because the company is expected to generate larger future cash flows.
    """)

with col2:
    st.warning("""
    Higher WACC generally decreases the estimated intrinsic value because future cash flows are discounted more heavily.
    """)

st.caption("Sensitivity analysis helps show how dependent a DCF model is on user assumptions.")
