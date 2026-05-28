# Stock Market Visualizer (Streamlit + yfinance)

## Project Overview

Stock Market Visualizer is a Python-based Streamlit application for analyzing, tracking, and visualizing stock market data using real-time and historical data from yfinance.

### Features

* Interactive candlestick charts using Plotly
* Technical indicators:

  * Moving Averages
  * RSI
  * Bollinger Bands
* Portfolio tracking via CSV/Excel upload
* Financial ratio analysis
* Stock correlation analysis
* Customizable chart controls
* Export charts as PNG or HTML
* Save and load user configurations
* GitHub integration workflow for collaboration


---

# app.py

```python
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
```

---

# utils/indicators.py

```python
import pandas as pd


def add_moving_averages(df, short_window=20, long_window=50):
    df[f"MA_{short_window}"] = df["Close"].rolling(window=short_window).mean()
    df[f"MA_{long_window}"] = df["Close"].rolling(window=long_window).mean()
    return df



def add_rsi(df, period=14):
    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    return df



def add_bollinger_bands(df, window=20):
    rolling_mean = df["Close"].rolling(window).mean()
    rolling_std = df["Close"].rolling(window).std()

    df["BB_Upper"] = rolling_mean + (rolling_std * 2)
    df["BB_Lower"] = rolling_mean - (rolling_std * 2)

    return df
```

---

# utils/charts.py

```python
import plotly.graph_objects as go



def create_candlestick_chart(
    df,
    ticker,
    show_ma=True,
    show_bb=True,
    theme="plotly",
    ma_short=20,
    ma_long=50,
):

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker,
        )
    )

    if show_ma:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f"MA_{ma_short}"],
                mode="lines",
                name=f"MA {ma_short}",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[f"MA_{ma_long}"],
                mode="lines",
                name=f"MA {ma_long}",
            )
        )

    if show_bb:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_Upper"],
                mode="lines",
                name="BB Upper",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["BB_Lower"],
                mode="lines",
                name="BB Lower",
            )
        )

    fig.update_layout(
        title=f"{ticker} Stock Analysis",
        template=theme,
        xaxis_rangeslider_visible=False,
        height=700,
    )

    return fig



def create_correlation_heatmap(df):
    correlation = df.corr()

    fig = go.Figure(
        data=go.Heatmap(
            z=correlation.values,
            x=correlation.columns,
            y=correlation.columns,
        )
    )

    fig.update_layout(
        title="Portfolio Correlation Heatmap"
    )

    return fig
```

---

# utils/portfolio.py

```python
import pandas as pd



def load_portfolio(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file)
```

---

# utils/config_manager.py

```python
import json
import os

CONFIG_FILE = "config/saved_configs.json"



def save_config(name, config):
    os.makedirs("config", exist_ok=True)

    configs = {}

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            configs = json.load(f)

    configs[name] = config

    with open(CONFIG_FILE, "w") as f:
        json.dump(configs, f, indent=4)



def load_configs():
    if not os.path.exists(CONFIG_FILE):
        return {}

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)
```

---

# README.md

````markdown
# Stock Market Visualizer

A Streamlit-powered stock market analysis dashboard using yfinance and Plotly.

## Features

- Real-time stock market analysis
- Candlestick charts
- Technical indicators
- Portfolio tracking
- Correlation analysis
- Financial ratios
- Config save/load
- Chart exporting

## Installation

```bash
git clone https://github.com/yourusername/stock-market-visualizer.git
cd stock-market-visualizer
````

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

## Portfolio File Format

CSV or Excel format:

```csv
Ticker,Shares
AAPL,10
MSFT,5
TSLA,3
```

## Deployment Options

* Streamlit Community Cloud
* Render
* Railway
* AWS EC2
* Docker

## GitHub Workflow

Initialize git:

```bash
git init
```

Add files:

```bash
git add .
```

Commit:

```bash
git commit -m "Initial commit"
```

Create GitHub repository and push:

```bash
git remote add origin https://github.com/yourusername/stock-market-visualizer.git
git branch -M main
git push -u origin main
```

````

---

# Recommended Enhancements

## Advanced Features

- Live WebSocket market feeds
- AI-based trend prediction
- News sentiment analysis
- Multi-portfolio support
- Dark/light theme toggle
- Authentication system
- Watchlists and alerts
- Backtesting strategies
- Monte Carlo portfolio simulation

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Deploy app

### Docker

```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
````

---

# GitHub Best Practices

* Use feature branches
* Add pull request templates
* Configure GitHub Actions for CI/CD
* Add unit tests with pytest
* Protect main branch
* Use semantic versioning

Example GitHub Actions workflow:

```yaml
name: Streamlit CI

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run basic check
        run: |
          python -m py_compile app.py
```
