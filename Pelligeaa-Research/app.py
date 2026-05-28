import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import json
import os

from utils.indicators import add_moving_averages, add_rsi, add_bollinger_bands
from utils.portfolio import load_portfolio
from utils.charts import create_candlestick_chart, create_correlation_heatmap
from utils.config_manager import save_config, load_configs

st.set_page_config(page_title="Stock Market Visualizer", layout="wide")

st.title("📈 Stock Market Visualizer")

# Sidebar Controls
st.sidebar.header("Chart Settings")

ticker = st.sidebar.text_input("Stock Ticker", value="AAPL")
period = st.sidebar.selectbox(
    "Timeframe",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3,
)

interval = st.sidebar.selectbox(
    "Interval",
    ["1d", "1wk", "1mo"],
    index=0,
)

show_ma = st.sidebar.checkbox("Show Moving Averages", value=True)
show_rsi = st.sidebar.checkbox("Show RSI", value=True)
show_bb = st.sidebar.checkbox("Show Bollinger Bands", value=True)

ma_short = st.sidebar.slider("Short MA", 5, 50, 20)
ma_long = st.sidebar.slider("Long MA", 20, 200, 50)

chart_theme = st.sidebar.selectbox(
    "Chart Theme",
    ["plotly", "plotly_dark", "ggplot2", "seaborn"],
)

# Download Data
@st.cache_data

def load_stock_data(symbol, period, interval):
    return yf.download(symbol, period=period, interval=interval)

try:
    df = load_stock_data(ticker, period, interval)

    if df.empty:
        st.error("No data found for ticker.")
        st.stop()

    # Add Indicators
    if show_ma:
        df = add_moving_averages(df, ma_short, ma_long)

    if show_rsi:
        df = add_rsi(df)

    if show_bb:
        df = add_bollinger_bands(df)

    # Create Chart
    fig = create_candlestick_chart(
        df,
        ticker,
        show_ma=show_ma,
        show_bb=show_bb,
        theme=chart_theme,
        ma_short=ma_short,
        ma_long=ma_long,
    )

    st.plotly_chart(fig, use_container_width=True)

    # RSI Chart
    if show_rsi:
        st.subheader("Relative Strength Index (RSI)")

        rsi_fig = go.Figure()

        rsi_fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["RSI"],
                mode="lines",
                name="RSI",
            )
        )

        rsi_fig.add_hline(y=70, line_dash="dash", line_color="red")
        rsi_fig.add_hline(y=30, line_dash="dash", line_color="green")

        st.plotly_chart(rsi_fig, use_container_width=True)

    # Financial Ratios
    st.subheader("Financial Ratios")

    stock = yf.Ticker(ticker)
    info = stock.info

    ratios = {
        "Market Cap": info.get("marketCap"),
        "PE Ratio": info.get("trailingPE"),
        "Forward PE": info.get("forwardPE"),
        "Dividend Yield": info.get("dividendYield"),
        "EPS": info.get("trailingEps"),
        "Beta": info.get("beta"),
    }

    ratio_df = pd.DataFrame(ratios.items(), columns=["Metric", "Value"])
    st.dataframe(ratio_df, use_container_width=True)

    # Export Options
    st.subheader("Export Chart")

    html_file = "chart.html"
    png_file = "chart.png"

    fig.write_html(html_file)
    fig.write_image(png_file)

    with open(html_file, "rb") as f:
        st.download_button(
            label="Download HTML",
            data=f,
            file_name=html_file,
            mime="text/html",
        )

    with open(png_file, "rb") as f:
        st.download_button(
            label="Download PNG",
            data=f,
            file_name=png_file,
            mime="image/png",
        )

    # Save Configuration
    st.subheader("Save Configuration")

    config_name = st.text_input("Configuration Name")

    if st.button("Save Config"):
        config = {
            "ticker": ticker,
            "period": period,
            "interval": interval,
            "show_ma": show_ma,
            "show_rsi": show_rsi,
            "show_bb": show_bb,
            "ma_short": ma_short,
            "ma_long": ma_long,
            "theme": chart_theme,
        }

        save_config(config_name, config)
        st.success("Configuration saved successfully.")

    configs = load_configs()

    if configs:
        selected_config = st.selectbox(
            "Load Saved Configuration",
            list(configs.keys()),
        )

        if st.button("Load Config"):
            st.json(configs[selected_config])

    # Portfolio Upload
    st.subheader("Portfolio Tracking")

    uploaded_file = st.file_uploader(
        "Upload Portfolio CSV or Excel",
        type=["csv", "xlsx"],
    )

    if uploaded_file:
        portfolio_df = load_portfolio(uploaded_file)

        st.dataframe(portfolio_df, use_container_width=True)

        tickers = portfolio_df["Ticker"].tolist()

        price_data = pd.DataFrame()

        for t in tickers:
            temp = yf.download(t, period="6mo")["Close"]
            price_data[t] = temp

        corr_fig = create_correlation_heatmap(price_data)

        st.subheader("Stock Correlation Heatmap")
        st.plotly_chart(corr_fig, use_container_width=True)

except Exception as e:
    st.error(f"Application Error: {e}")
