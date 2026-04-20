def generate_signal(rsi: float, macd: float, macd_signal: float,
                    ema_9: float, ema_21: float, lsma_25: float = 0,
                    lsma_200: float = 0, adx: float = 0,
                    bb_pct_b: float = 0.5, volume_change: float = 0,
                    price: float = 0) -> dict:

    score = 0
    reasons = []

    # RSI
    if rsi < 30:
        score += 2
        reasons.append("RSI en sobreventa, posible rebote")
    elif rsi > 70:
        score -= 2
        reasons.append("RSI en sobrecompra, posible corrección")
    else:
        reasons.append("RSI en zona neutral")

    # MACD
    if macd > macd_signal:
        score += 1
        reasons.append("MACD con momentum alcista")
    else:
        score -= 1
        reasons.append("MACD con momentum bajista")

    # EMA
    if ema_9 > ema_21:
        score += 1
        reasons.append("EMA 9 sobre EMA 21, tendencia alcista de corto plazo")
    else:
        score -= 1
        reasons.append("EMA 9 bajo EMA 21, tendencia bajista de corto plazo")

    # LSMA
    if lsma_200 > 0 and price > 0:
        if price > lsma_200:
            score += 2
            reasons.append("Precio sobre LSMA 200, tendencia macro alcista")
        else:
            score -= 2
            reasons.append("Precio bajo LSMA 200, tendencia macro bajista")

    if lsma_25 > 0 and price > 0:
        if price > lsma_25:
            score += 1
            reasons.append("Precio sobre LSMA 25, momentum de mediano plazo positivo")
        else:
            score -= 1
            reasons.append("Precio bajo LSMA 25, momentum de mediano plazo negativo")

    # Bollinger
    if bb_pct_b < 0.1:
        score += 1
        reasons.append("Precio cerca de banda inferior de Bollinger, posible rebote")
    elif bb_pct_b > 0.9:
        score -= 1
        reasons.append("Precio cerca de banda superior de Bollinger, posible resistencia")

    # ADX
    trend_confirmed = adx > 25

    whale_signal = None
    if volume_change > 150:
        whale_signal = f"Volumen 24h con spike de +{volume_change:.0f}%, posible movimiento institucional"
        reasons.append(whale_signal)

    if score >= 3:
        action = "BUY"
    elif score <= -3:
        action = "SELL"
    else:
        action = "HOLD"

    base_confidence = min(0.4 + (abs(score) * 0.08), 0.90)
    if trend_confirmed:
        base_confidence = min(base_confidence + 0.05, 0.95)

    short_term  = _short_term_signal(rsi, macd, macd_signal, bb_pct_b)
    medium_term = _medium_term_signal(lsma_25, price, ema_21)
    long_term   = _long_term_signal(lsma_200, price, adx)

    return {
        "action": action,
        "confidence": round(base_confidence, 2),
        "explanation": " | ".join(reasons),
        "whale_activity": whale_signal,
        "horizons": {
            "short_term":  short_term,
            "medium_term": medium_term,
            "long_term":   long_term
        }
    }

def _short_term_signal(rsi, macd, macd_signal, bb_pct_b) -> dict:
    notes = []
    risk = "medio"

    if rsi > 70 or bb_pct_b > 0.9:
        notes.append("Alta volatilidad, riesgo elevado en corto plazo")
        risk = "alto"
        action = "SELL"
    elif rsi < 30:
        notes.append("Posible rebote en 1-7 días")
        risk = "bajo"
        action = "BUY"
    else:
        notes.append("Sin señales claras de corto plazo")
        action = "HOLD"

    if macd > macd_signal:
        notes.append("Momentum a favor en corto plazo")
    else:
        notes.append("Momentum en contra en corto plazo")

    return {
        "horizon": "1-7 días",
        "action":  action,
        "risk":    risk,
        "notes":   " | ".join(notes)
    }

def _medium_term_signal(lsma_25, price, ema_21) -> dict:
    if lsma_25 > 0 and price > 0:
        if price > lsma_25 and price > ema_21:
            action = "BUY"
            notes  = "Tendencia de mediano plazo positiva, posible continuación alcista"
        elif price < lsma_25:
            action = "SELL"
            notes  = "Por debajo de LSMA 25, cautela en 1-3 meses"
        else:
            action = "HOLD"
            notes  = "Señales mixtas en mediano plazo"
    else:
        action = "HOLD"
        notes  = "Datos insuficientes para proyección de mediano plazo"

    return {"horizon": "1-3 meses", "action": action, "notes": notes}

def _long_term_signal(lsma_200, price, adx) -> dict:
    notes = []

    if lsma_200 > 0 and price > 0:
        if price > lsma_200:
            action = "BUY"
            notes.append("Estructura de largo plazo alcista")
        else:
            action = "SELL"
            notes.append("Estructura de largo plazo bajista, evaluar fundamentos")
    else:
        action = "HOLD"
        notes.append("Sin datos suficientes de largo plazo")

    if adx > 40:
        notes.append("Tendencia fuerte y sostenida")
    elif adx < 20:
        notes.append("Mercado lateral, sin tendencia clara")

    return {"horizon": "+6 meses", "action": action, "notes": " | ".join(notes)}