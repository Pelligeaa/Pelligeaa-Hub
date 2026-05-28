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
