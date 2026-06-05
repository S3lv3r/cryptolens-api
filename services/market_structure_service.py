import numpy as np
from services.binance_service import fetch_klines

DIRECTION_LABELS = {
    "bullish": "Alcista",
    "bearish": "Bajista"
}

CHOCH_TYPE_LABELS = {
    "lower_high": "Máximo más bajo",
    "higher_low": "Mínimo más alto"
}

STRUCTURE_LABELS = {
    "uptrend": "Tendencia alcista",
    "downtrend": "Tendencia bajista",
    "transition": "Transición",
    "ranging": "Rango lateral",
    "undefined": "Indefinida"
}

TREND_PHASE_LABELS = {
    "continuation": "Continuación",
    "reversal": "Reversión",
    "consolidation": "Consolidación",
    "unknown": "Desconocida"
}

def find_swing_highs(highs: list, window: int = 3) -> list:
    swings = []
    for i in range(window, len(highs) - window):
        if all(highs[i] > highs[i-j] for j in range(1, window+1)) and \
           all(highs[i] > highs[i+j] for j in range(1, window+1)):
            swings.append({"index": i, "price": highs[i]})
    return swings

def find_swing_lows(lows: list, window: int = 3) -> list:
    swings = []
    for i in range(window, len(lows) - window):
        if all(lows[i] < lows[i-j] for j in range(1, window+1)) and \
           all(lows[i] < lows[i+j] for j in range(1, window+1)):
            swings.append({"index": i, "price": lows[i]})
    return swings

def detect_bos(swing_highs: list, swing_lows: list, closes: list, volumes: list) -> dict:

    bos = {"detected": False, "price": None, "direction": None}

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return bos

    last_high = swing_highs[-1]["price"]
    last_low  = swing_lows[-1]["price"]
    current_close = closes[-1]
    avg_volume = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else 0
    current_volume = volumes[-1]
    volume_confirmed = current_volume > avg_volume * 1.2

    if current_close > last_high and volume_confirmed:
        bos = {"detected": True, "price": last_high, "direction": "bullish", "direction_label": "Alcista"}
    elif current_close < last_low and volume_confirmed:
        bos = {"detected": True, "price": last_low, "direction": "bearish", "direction_label": "Bajista"}

    return bos

def detect_choch(swing_highs: list, swing_lows: list) -> dict:

    choch = {"detected": False, "price": None, "direction": None}

    if len(swing_highs) < 3 or len(swing_lows) < 3:
        return choch

    if swing_highs[-1]["price"] < swing_highs[-2]["price"]:
        choch = {
            "detected":  True,
            "price":     swing_highs[-1]["price"],
            "direction": "bearish",
            "direction_label": "Bajista",
            "type":      "lower_high",
            "type_label": "Máximo más bajo"
        }
    elif swing_lows[-1]["price"] > swing_lows[-2]["price"]:
        choch = {
            "detected":  True,
            "price":     swing_lows[-1]["price"],
            "direction": "bullish",
            "direction_label": "Alcista",
            "type":      "higher_low",
            "type_label": "Mínimo más alto"
        }

    return choch

def detect_market_structure(symbol: str, timeframe: str = "1d") -> dict:

    klines = fetch_klines(symbol, timeframe, limit=100)
    if len(klines) < 20:
        return {"error": "Datos insuficientes"}

    closes  = [k["close"]  for k in klines]
    highs   = [k["high"]   for k in klines]
    lows    = [k["low"]    for k in klines]
    volumes = [k["volume"] for k in klines]
    price   = closes[-1]

    swing_highs = find_swing_highs(highs)
    swing_lows  = find_swing_lows(lows)
    bos         = detect_bos(swing_highs, swing_lows, closes, volumes)
    choch       = detect_choch(swing_highs, swing_lows)

    resistance = min(
        [s["price"] for s in swing_highs if s["price"] > price],
        default=None
    )
    support = max(
        [s["price"] for s in swing_lows if s["price"] < price],
        default=None
    )

    liq_high = max([s["price"] for s in swing_highs[-5:]], default=None)
    liq_low  = min([s["price"] for s in swing_lows[-5:]],  default=None)

    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        hh = swing_highs[-1]["price"] > swing_highs[-2]["price"]
        hl = swing_lows[-1]["price"]  > swing_lows[-2]["price"]
        lh = swing_highs[-1]["price"] < swing_highs[-2]["price"]
        ll = swing_lows[-1]["price"]  < swing_lows[-2]["price"]

        if hh and hl:
            structure   = "uptrend"
            trend_phase = "continuation"
        elif lh and ll:
            structure   = "downtrend"
            trend_phase = "continuation"
        elif choch["detected"]:
            structure   = "transition"
            trend_phase = "reversal"
        else:
            structure   = "ranging"
            trend_phase = "consolidation"
    else:
        structure   = "undefined"
        trend_phase = "unknown"

    return {
        "symbol":             symbol,
        "timeframe":          timeframe,
        "current_price":      round(price, 6),
        "market_structure":   structure,
        "market_structure_label": STRUCTURE_LABELS.get(structure, structure),
        "trend_phase":        trend_phase,
        "trend_phase_label":  TREND_PHASE_LABELS.get(trend_phase, trend_phase),
        "swing_high":         swing_highs[-1]["price"] if swing_highs else None,
        "swing_low":          swing_lows[-1]["price"]  if swing_lows  else None,
        "current_resistance": round(resistance, 6) if resistance else None,
        "current_support":    round(support, 6)    if support    else None,
        "liquidity_zone_high":round(liq_high, 6)   if liq_high   else None,
        "liquidity_zone_low": round(liq_low, 6)    if liq_low    else None,
        "last_bos":           bos,
        "last_choch":         choch,
        "swing_highs_count":  len(swing_highs),
        "swing_lows_count":   len(swing_lows)
    }
