import streamlit as st

st.set_page_config(
    page_title="FINA 4011 Equity Valuation App",
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
    font-size: 48px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 20px;
    color: #475569;
    margin-bottom: 25px;
}

.card {
    background-color: white;
    padding: 24px;
    border-radius: 18px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

.section-title {
    color: #0f172a;
    font-size: 24px;
    font-weight: 700;
}

.text {
    color: #475569;
    font-size: 16px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="main-title">📊 FINA 4011 Equity Valuation App</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">A Streamlit app for estimating the intrinsic value of a stock using a Discounted Cash Flow model.</div>',
    unsafe_allow_html=True
)

# -----------------------------
# Main Content
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <div class="section-title">What This App Does</div>
        <p class="text">
        This app helps investors estimate the intrinsic value of a stock using a Discounted Cash Flow model.
        The user can enter a stock ticker, adjust valuation assumptions, and compare the estimated value to the current market price.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="section-title">Default Company</div>
        <p class="text">
        The app defaults to Taiwan Semiconductor Manufacturing Company, ticker TSM.
        TSM is a strong example because it is highly relevant to AI, global chip demand, and long-term growth investing.
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <div class="section-title">How to Use the App</div>
    <p class="text">
    Use the sidebar to move through each page. Start with the Valuation page to enter assumptions and calculate intrinsic value.
    Then use the Market Data page to view recent stock performance, the Model Breakdown page to understand the formulas,
    and the Sensitivity Analysis page to see how changes in assumptions affect the final valuation.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
    <div class="section-title">Pages Included</div>
    <ul class="text">
        <li><b>Valuation:</b> Main DCF model and intrinsic value estimate</li>
        <li><b>Market Data:</b> Historical stock price data and return trends</li>
        <li><b>Model Breakdown:</b> Step-by-step explanation of the valuation logic</li>
        <li><b>Sensitivity Analysis:</b> Shows how the valuation changes when assumptions change</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.info("Use the sidebar on the left to move between pages.")
st.caption("Created for FINA 4011 Project 2.")
