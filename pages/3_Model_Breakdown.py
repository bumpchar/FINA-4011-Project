import streamlit as st

st.set_page_config(
    page_title="Model Breakdown",
    page_icon="🧠",
    layout="wide"
)

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
.formula {
    background-color: #f1f5f9;
    padding: 12px;
    border-radius: 10px;
    font-family: monospace;
    color: #0f172a;
}
</style>
""", unsafe_allow_html=True)

st.title("🧠 Model Breakdown")
st.write("This page explains how the DCF model works step by step.")

st.markdown("""
<div class="card">
<h3>1. Revenue Projection</h3>
<p>The model starts with current revenue and grows it each year using the selected annual growth rate.</p>
<div class="formula">Revenue next year = Revenue this year × (1 + Growth Rate)</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h3>2. EBIT</h3>
<p>EBIT means Earnings Before Interest and Taxes. The app estimates operating income by applying the EBIT margin to revenue.</p>
<div class="formula">EBIT = Revenue × EBIT Margin</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h3>3. NOPAT</h3>
<p>NOPAT means Net Operating Profit After Taxes. This estimates after-tax operating profit before considering financing decisions.</p>
<div class="formula">NOPAT = EBIT × (1 − Tax Rate)</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h3>4. Free Cash Flow</h3>
<p>Free Cash Flow is the cash available after the company reinvests back into operations.</p>
<div class="formula">Free Cash Flow = NOPAT − Reinvestment</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h3>5. Present Value of Cash Flows</h3>
<p>Future cash flows are discounted back to today because money received in the future is worth less than money received today.</p>
<div class="formula">PV of FCF = FCF ÷ (1 + WACC)^Year</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h3>6. Terminal Value</h3>
<p>Terminal value estimates the company’s value after the forecast period. This is important because companies are expected to keep operating beyond the explicit projection years.</p>
<div class="formula">Terminal Value = Final Year FCF × (1 + Terminal Growth) ÷ (WACC − Terminal Growth)</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h3>7. Enterprise Value</h3>
<p>Enterprise value combines the present value of projected free cash flows and the present value of terminal value.</p>
<div class="formula">Enterprise Value = PV of Projected FCF + PV of Terminal Value</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h3>8. Equity Value</h3>
<p>Equity value adjusts enterprise value by subtracting debt and adding cash.</p>
<div class="formula">Equity Value = Enterprise Value − Debt + Cash</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="card">
<h3>9. Intrinsic Value Per Share</h3>
<p>The final equity value is divided by shares outstanding to estimate what one share may be worth.</p>
<div class="formula">Intrinsic Value Per Share = Equity Value ÷ Shares Outstanding</div>
</div>
""", unsafe_allow_html=True)

st.subheader("Why This Page Matters")

st.info("""
This page helps meet the explainability part of the project. Instead of only showing a final number,
the app shows the logic behind the valuation so users understand how each input affects the result.
""")
