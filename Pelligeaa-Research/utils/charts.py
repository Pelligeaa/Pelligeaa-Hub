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
