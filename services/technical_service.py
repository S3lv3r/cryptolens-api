import pandas as pd
import numpy as np

def calculate_ema(prices: list, period: int) -> float:
    series = pd.Series(prices)
    return round(series.ewm(span=period, adjust=False).mean().iloc[-1], 6)

def calculate_rsi(prices: list, period: int = 14) -> float:
    series = pd.Series(prices)
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss
    rsi   = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2)

def calculate_macd(prices: list) -> dict:
    series     = pd.Series(prices)
    ema12      = series.ewm(span=12, adjust=False).mean()
    ema26      = series.ewm(span=26, adjust=False).mean()
    macd_line  = ema12 - ema26
    signal_line= macd_line.ewm(span=9, adjust=False).mean()
    histogram  = macd_line - signal_line
    return {
        "macd":      round(macd_line.iloc[-1], 6),
        "signal":    round(signal_line.iloc[-1], 6),
        "histogram": round(histogram.iloc[-1], 6)
    }

def calculate_lsma(prices: list, period: int) -> float:
    if len(prices) < period:
        return 0.0
    series = pd.Series(prices[-period:])
    x      = np.arange(period)
    slope, intercept = np.polyfit(x, series, 1)
    return round(slope * (period - 1) + intercept, 6)

def calculate_bollinger_bands(prices: list, period: int = 20, std_dev: float = 2.0) -> dict:
    series     = pd.Series(prices)
    sma        = series.rolling(period).mean()
    std        = series.rolling(period).std()
    upper      = (sma + std * std_dev).iloc[-1]
    middle     = sma.iloc[-1]
    lower      = (sma - std * std_dev).iloc[-1]
    price      = prices[-1]
    bandwidth  = (upper - lower) / middle if middle != 0 else 0
    pct_b      = (price - lower) / (upper - lower) if (upper - lower) != 0 else 0.5

    return {
        "upper":     round(upper, 6),
        "middle":    round(middle, 6),
        "lower":     round(lower, 6),
        "bandwidth": round(bandwidth, 4),
        "pct_b":     round(pct_b, 4)
    }

def calculate_adx_ohlcv(highs: list, lows: list, closes: list, period: int = 14) -> dict:
    if len(closes) < period * 2:
        return {"adx": 0.0, "trend_strength": "datos insuficientes"}

    high  = pd.Series(highs)
    low   = pd.Series(lows)
    close = pd.Series(closes)

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)

    plus_dm  = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm  < 0] = 0
    minus_dm[minus_dm < 0] = 0

    atr      = tr.ewm(span=period, adjust=False).mean()
    plus_di  = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)

    dx       = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1)) * 100
    adx_val  = round(dx.ewm(span=period, adjust=False).mean().iloc[-1], 2)

    if adx_val < 20:
        strength = "tendencia débil o lateral"
    elif adx_val < 40:
        strength = "tendencia moderada"
    elif adx_val < 60:
        strength = "tendencia fuerte"
    else:
        strength = "tendencia muy fuerte"

    return {"adx": adx_val, "trend_strength": strength}