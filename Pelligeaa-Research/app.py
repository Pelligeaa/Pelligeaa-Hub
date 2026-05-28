import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import os

from utils.indicators import (
    add_moving_averages,
    add_rsi,
    add_bollinger_bands,
)

from utils.portfolio import load_portfolio

from utils.charts import (
    create_candlestick_chart,
    create_correlation_heatmap,
)

from utils.config_manager import (
    save_config,
    load_configs,
)

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Stock Market Visualizer",
    layout="wide",
)

st.title("📈 Stock Market Visualizer")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

st.sidebar.header("Chart Settings")

ticker = st.sidebar.text_input(
    "Stock Ticker",
    value="AAPL",
)

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

show_ma = st.sidebar.checkbox(
    "Show Moving Averages",
    value=True,
)

show_rsi = st.sidebar.checkbox(
    "Show RSI",
    value=True,
)

show_bb = st.sidebar.checkbox(
    "Show Bollinger Bands",
    value=True,
)

ma_short = st.sidebar.slider(
    "Short Moving Average",
    5,
    50,
    20,
)

ma_long = st.sidebar.slider(
    "Long Moving Average",
    20,
    200,
    50,
)

chart_theme = st.sidebar.selectbox(
    "Chart Theme",
    ["plotly", "plotly_dark", "ggplot2", "seaborn"],
)

# ---------------------------------------------------
# STOCK DATA FUNCTION
# ---------------------------------------------------

@st.cache_data
def load_stock_data(symbol, period, interval):

    try:

        symbol = symbol.strip().upper()

        df = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            return pd.DataFrame()

        # Fix MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Remove bad rows
        df = df.dropna(subset=["Close"])

        return df

    except Exception as e:
        st.error(f"Yahoo Finance Error: {e}")
        return pd.DataFrame()

# ---------------------------------------------------
# MAIN APP
# ---------------------------------------------------

try:

    df = load_stock_data(
        ticker,
        period,
        interval,
    )

    if df.empty:
        st.error(
            f"No data found for ticker '{ticker}'. "
            "Try AAPL, MSFT, NVDA, TSLA, or SPY."
        )
        st.stop()

    # ---------------------------------------------------
    # TECHNICAL INDICATORS
    # ---------------------------------------------------

    if show_ma:
        df = add_moving_averages(
            df,
            ma_short,
            ma_long,
        )

    if show_rsi:
        df = add_rsi(df)

    if show_bb:
        df = add_bollinger_bands(df)

    # ---------------------------------------------------
    # MAIN CHART
    # ---------------------------------------------------

    fig = create_candlestick_chart(
        df=df,
        ticker=ticker,
        show_ma=show_ma,
        show_bb=show_bb,
        theme=chart_theme,
        ma_short=ma_short,
        ma_long=ma_long,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # ---------------------------------------------------
    # RSI CHART
    # ---------------------------------------------------

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

        rsi_fig.add_hline(
            y=70,
            line_dash="dash",
            line_color="red",
        )

        rsi_fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="green",
        )

        st.plotly_chart(
            rsi_fig,
            use_container_width=True,
        )

    # ---------------------------------------------------
    # FINANCIAL RATIOS
    # ---------------------------------------------------

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

    ratio_df = pd.DataFrame(
        ratios.items(),
        columns=["Metric", "Value"],
    )

    st.dataframe(
        ratio_df,
        use_container_width=True,
    )

    # ---------------------------------------------------
    # EXPORT OPTIONS
    # ---------------------------------------------------

    st.subheader("Export Chart")

    html_file = "chart.html"
    png_file = "chart.png"

    fig.write_html(html_file)

    try:
        fig.write_image(png_file)

    except Exception:
        st.warning(
            "PNG export requires kaleido. "
            "Install using: pip install kaleido"
        )

    # HTML DOWNLOAD

    with open(html_file, "rb") as f:

        st.download_button(
            label="Download HTML",
            data=f,
            file_name=html_file,
            mime="text/html",
        )

    # PNG DOWNLOAD

    if os.path.exists(png_file):

        with open(png_file, "rb") as f:

            st.download_button(
                label="Download PNG",
                data=f,
                file_name=png_file,
                mime="image/png",
            )

    # ---------------------------------------------------
    # SAVE CONFIGURATION
    # ---------------------------------------------------

    st.subheader("Save Configuration")

    config_name = st.text_input(
        "Configuration Name"
    )

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

        save_config(
            config_name,
            config,
        )

        st.success(
            "Configuration saved successfully."
        )

    configs = load_configs()

    if configs:

        selected_config = st.selectbox(
            "Load Saved Configuration",
            list(configs.keys()),
        )

        if st.button("Load Config"):

            st.json(
                configs[selected_config]
            )

    # ---------------------------------------------------
    # PORTFOLIO TRACKING
    # ---------------------------------------------------

    st.subheader("Portfolio Tracking")

    uploaded_file = st.file_uploader(
        "Upload Portfolio CSV or Excel",
        type=["csv", "xlsx"],
    )

    if uploaded_file:

        portfolio_df = load_portfolio(
            uploaded_file
        )

        st.dataframe(
            portfolio_df,
            use_container_width=True,
        )

        if "Ticker" not in portfolio_df.columns:

            st.error(
                "Portfolio file must contain "
                "a 'Ticker' column."
            )

        else:

            tickers = portfolio_df["Ticker"].tolist()

            price_data = pd.DataFrame()

            for t in tickers:

                try:

                    temp_df = yf.download(
                        t,
                        period="6mo",
                        auto_adjust=False,
                        progress=False,
                        threads=False,
                    )

                    if (
                        isinstance(
                            temp_df.columns,
                            pd.MultiIndex,
                        )
                    ):
                        temp_df.columns = (
                            temp_df.columns.get_level_values(0)
                        )

                    if not temp_df.empty:

                        price_data[t] = temp_df["Close"]

                except Exception:
                    pass

            if not price_data.empty:

                corr_fig = create_correlation_heatmap(
                    price_data
                )

                st.subheader(
                    "Stock Correlation Heatmap"
                )

                st.plotly_chart(
                    corr_fig,
                    use_container_width=True,
                )

except Exception as e:

    st.error(
        f"Application Error: {e}"
    )
