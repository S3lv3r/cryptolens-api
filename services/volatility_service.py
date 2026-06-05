import numpy as np
from services.binance_service import fetch_klines

VOLATILITY_REGIME_LABELS = {
    "low_volatility": "Baja volatilidad",
    "high_volatility": "Alta volatilidad",
    "normal": "Normal"
}

def calculate_historical_volatility(closes: list, period: int = 30) -> float:
    if len(closes) < period + 1:
        return 0.0
    returns = np.diff(np.log(closes[-period-1:]))
    return round(float(np.std(returns) * np.sqrt(365) * 100), 4)

def calculate_volatility_percentile(closes: list, current_vol: float, lookback: int = 90) -> float:
    if len(closes) < lookback + 1:
        return 50.0
    vols = []
    for i in range(lookback, len(closes)):
        window  = closes[i-30:i]
        returns = np.diff(np.log(window))
        vol     = float(np.std(returns) * np.sqrt(365) * 100) if len(returns) > 1 else 0
        vols.append(vol)
    if not vols:
        return 50.0
    pct = sum(1 for v in vols if v < current_vol) / len(vols) * 100
    return round(pct, 2)

def get_volatility_regime(percentile: float) -> str:
    if percentile < 25:
        return "low_volatility"
    elif percentile > 75:
        return "high_volatility"
    else:
        return "normal"

def analyze_volatility(symbol: str, timeframe: str = "1d") -> dict:
    klines = fetch_klines(symbol, timeframe, limit=150)
    if len(klines) < 30:
        return {"error": "Datos insuficientes"}

    closes = [k["close"] for k in klines]
    highs  = [k["high"]  for k in klines]
    lows   = [k["low"]   for k in klines]
    price  = closes[-1]

    import pandas as pd
    high_s  = pd.Series(highs)
    low_s   = pd.Series(lows)
    close_s = pd.Series(closes)
    tr = pd.concat([
        high_s - low_s,
        (high_s - close_s.shift()).abs(),
        (low_s  - close_s.shift()).abs()
    ], axis=1).max(axis=1)
    atr = round(float(tr.rolling(14).mean().iloc[-1]), 6)
    atr_pct = round((atr / price) * 100, 4) if price else 0

    hist_vol   = calculate_historical_volatility(closes)
    vol_pct    = calculate_volatility_percentile(closes, hist_vol)
    regime     = get_volatility_regime(vol_pct)

    if regime == "high_volatility":
        condition = "Mercado con alta volatilidad. Señales menos confiables, ajustar tamaño de posición."
    elif regime == "low_volatility":
        condition = "Mercado tranquilo. Posible expansión de volatilidad próxima. Breakout potencial."
    else:
        condition = "Volatilidad normal. Condiciones estándar de mercado."

    return {
        "symbol":               symbol,
        "timeframe":            timeframe,
        "current_price":        round(price, 6),
        "atr":                  atr,
        "atr_pct":              atr_pct,
        "historical_volatility":hist_vol,
        "volatility_percentile":vol_pct,
        "regime":               regime,
        "regime_label":         VOLATILITY_REGIME_LABELS.get(regime, regime),
        "market_condition":     condition
    }
