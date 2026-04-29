import streamlit as st

st.set_page_config(page_title="FINA 4011 DCF Valuation App", layout="wide")

st.title("FINA 4011 DCF Valuation App")
st.write("This app will estimate the intrinsic value of a stock using a DCF model.")

ticker = st.text_input("Enter Stock Ticker", value="AAPL")

st.write(f"You selected: {ticker}")
