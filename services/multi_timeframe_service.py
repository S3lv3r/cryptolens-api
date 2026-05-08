import numpy as np
import pandas as pd
from datetime import datetime
from services.binance_service import fetch_klines
from services.technical_service import (
    calculate_ema, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_adx_ohlcv
)

def calculate_atr(highs: list, lows: list, closes: list, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 0.0
    high  = pd.Series(highs)
    low   = pd.Series(lows)
    close = pd.Series(closes)
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return round(tr.rolling(period).mean().iloc[-1], 6)

def determine_trend(ema_9, ema_21, ema_50, ema_200, price, macd, macd_signal) -> dict:
    bullish_signals = 0
    bearish_signals = 0

    if price > ema_9:   bullish_signals += 1
    else:               bearish_signals += 1
    if price > ema_21:  bullish_signals += 1
    else:               bearish_signals += 1
    if price > ema_50:  bullish_signals += 1
    else:               bearish_signals += 1
    if price > ema_200: bullish_signals += 1
    else:               bearish_signals += 1
    if macd > macd_signal: bullish_signals += 1
    else:                  bearish_signals += 1

    total = bullish_signals + bearish_signals
    ratio = bullish_signals / total if total > 0 else 0.5

    if ratio >= 0.8:
        direction = "strong_bullish"
        strength  = "strong"
    elif ratio >= 0.6:
        direction = "bullish"
        strength  = "moderate"
    elif ratio <= 0.2:
        direction = "strong_bearish"
        strength  = "strong"
    elif ratio <= 0.4:
        direction = "bearish"
        strength  = "moderate"
    else:
        direction = "neutral"
        strength  = "weak"

    return {"direction": direction, "strength": strength, "bull_ratio": round(ratio, 2)}

def determine_market_condition(rsi, bb_pct_b, atr, adx) -> str:
    if rsi > 75 and bb_pct_b > 0.9:
        return "high_volatility"
    elif rsi < 25 and bb_pct_b < 0.1:
        return "high_volatility"
    elif adx < 20:
        return "low_volatility"
    else:
        return "normal"

def analyze_timeframe(symbol: str, timeframe: str) -> dict | None:
    limit_map = {
        "15m": 200,
        "1h":  200,
        "4h":  200,
        "1d":  200,
        "1w":  100
    }
    limit  = limit_map.get(timeframe, 200)
    klines = fetch_klines(symbol, timeframe, limit=limit)

    if len(klines) < 50:
        print(f"  ⚠️  {symbol} {timeframe}: datos insuficientes ({len(klines)})")
        return None

    closes = [k["close"]  for k in klines]
    highs  = [k["high"]   for k in klines]
    lows   = [k["low"]    for k in klines]
    price  = closes[-1]

    # Indicadores
    ema_9   = calculate_ema(closes, 9)
    ema_21  = calculate_ema(closes, 21)
    ema_50  = calculate_ema(closes, 50)
    ema_200 = calculate_ema(closes, 200) if len(closes) >= 200 else 0
    rsi     = calculate_rsi(closes)
    macd_d  = calculate_macd(closes)
    bb      = calculate_bollinger_bands(closes)
    adx_d   = calculate_adx_ohlcv(highs, lows, closes)
    atr     = calculate_atr(highs, lows, closes)
    trend   = determine_trend(ema_9, ema_21, ema_50, ema_200, price, macd_d["macd"], macd_d["signal"])
    cond    = determine_market_condition(rsi, bb["pct_b"], atr, adx_d["adx"])

    return {
        "timeframe":       timeframe,
        "timestamp":       datetime.utcnow().isoformat(),
        "price":           round(price, 6),
        "rsi":             rsi,
        "macd":            macd_d["macd"],
        "macd_signal":     macd_d["signal"],
        "macd_histogram":  macd_d["histogram"],
        "ema_9":           ema_9,
        "ema_21":          ema_21,
        "ema_50":          ema_50,
        "ema_200":         ema_200,
        "adx":             adx_d["adx"],
        "bb_upper":        bb["upper"],
        "bb_middle":       bb["middle"],
        "bb_lower":        bb["lower"],
        "bb_pct_b":        bb["pct_b"],
        "atr":             atr,
        "trend_direction": trend["direction"],
        "trend_strength":  trend["strength"],
        "market_condition":cond
    }

def calculate_consensus(analyses: dict) -> dict:
    """
    Calcula consenso global entre todos los timeframes.
    bullish si >= 60% alcistas, bearish si >= 60% bajistas.
    """
    if not analyses:
        return {"bias": "neutral", "alignment_score": 0.0, "confidence": 0.0}

    bullish_tfs = []
    bearish_tfs = []
    neutral_tfs = []
    alignment_scores = []

    for tf, data in analyses.items():
        if data is None:
            continue
        direction = data["trend_direction"]
        if "bullish" in direction:
            bullish_tfs.append(tf)
            alignment_scores.append(1.0)
        elif "bearish" in direction:
            bearish_tfs.append(tf)
            alignment_scores.append(0.0)
        else:
            neutral_tfs.append(tf)
            alignment_scores.append(0.5)

    total = len(bullish_tfs) + len(bearish_tfs) + len(neutral_tfs)
    if total == 0:
        return {"bias": "neutral", "alignment_score": 0.0, "confidence": 0.0}

    bull_pct = len(bullish_tfs) / total
    bear_pct = len(bearish_tfs) / total

    if bull_pct >= 0.6:
        bias = "bullish"
    elif bear_pct >= 0.6:
        bias = "bearish"
    else:
        bias = "neutral"

    avg = sum(alignment_scores) / len(alignment_scores)
    alignment = 1.0 - (2 * abs(avg - 0.5))

    return {
        "bias":            bias,
        "alignment_score": round(alignment, 3),
        "confidence":      round(bull_pct if bias == "bullish" else bear_pct if bias == "bearish" else 0.5, 3),
        "bullish_timeframes": bullish_tfs,
        "bearish_timeframes": bearish_tfs,
        "neutral_timeframes": neutral_tfs,
        "timeframes_analyzed": total
    }