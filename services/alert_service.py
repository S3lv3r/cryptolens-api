from datetime import datetime, timedelta
from database import SessionLocal
from models import Crypto, Signal, MarketData, TechnicalIndicator, Alert
from services.market_structure_service import detect_market_structure

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]

ACTION_LABELS = {
    "BUY": "Comprar",
    "SELL": "Vender",
    "HOLD": "Esperar"
}

SEVERITY_LABELS = {
    "low": "Baja",
    "medium": "Media",
    "high": "Alta",
    "critical": "Crítica"
}

ALERT_TYPE_LABELS = {
    "signal_change": "Cambio de señal",
    "rsi_overbought": "RSI en sobrecompra",
    "rsi_oversold": "RSI en sobreventa",
    "volume_spike": "Aumento inusual de volumen",
    "price_at_support": "Precio en soporte",
    "price_at_resistance": "Precio en resistencia",
    "break_of_structure": "Ruptura de estructura",
    "extreme_price_move": "Movimiento extremo de precio"
}

DIRECTION_LABELS = {
    "bullish": "alcista",
    "bearish": "bajista"
}

def _action_label(action: str | None) -> str | None:
    return ACTION_LABELS.get(action, action) if action else None

def detect_alerts_for_symbol(symbol: str) -> list:
    """
    Detecta condiciones notables para un activo y genera alertas.
    No requiere configuración — la API detecta automáticamente.
    """
    db = SessionLocal()
    alerts = []

    try:
        crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
        if not crypto:
            return []

        market = (
            db.query(MarketData)
            .filter(MarketData.crypto_id == crypto.id)
            .order_by(MarketData.timestamp.desc())
            .first()
        )
        signal = (
            db.query(Signal)
            .filter(Signal.crypto_id == crypto.id)
            .order_by(Signal.timestamp.desc())
            .first()
        )
        ind = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.crypto_id == crypto.id)
            .order_by(TechnicalIndicator.timestamp.desc())
            .first()
        )

        prev_signal = (
            db.query(Signal)
            .filter(Signal.crypto_id == crypto.id)
            .order_by(Signal.timestamp.desc())
            .offset(1)
            .first()
        )

        if not market or not signal or not ind:
            return []

        price = market.price_usd

        if prev_signal and signal.action != prev_signal.action:
            previous_label = _action_label(prev_signal.action)
            current_label = _action_label(signal.action)
            alerts.append({
                "symbol":     symbol,
                "alert_type": "signal_change",
                "alert_type_label": ALERT_TYPE_LABELS["signal_change"],
                "severity":   "high",
                "severity_label": SEVERITY_LABELS["high"],
                "title":      f"{symbol} cambió señal: {previous_label} -> {current_label}",
                "message":    f"La señal de {symbol} cambió de {previous_label} a {current_label} con confianza del {signal.confidence:.0%}. {signal.explanation}",
                "data": {
                    "previous": prev_signal.action,
                    "current":  signal.action,
                    "previous_label": previous_label,
                    "current_label": current_label,
                    "confidence": signal.confidence
                }
            })

        if ind.rsi:
            if ind.rsi >= 75:
                alerts.append({
                    "symbol":     symbol,
                    "alert_type": "rsi_overbought",
                    "alert_type_label": ALERT_TYPE_LABELS["rsi_overbought"],
                    "severity":   "high" if ind.rsi >= 80 else "medium",
                    "severity_label": SEVERITY_LABELS["high" if ind.rsi >= 80 else "medium"],
                    "title":      f"{symbol} RSI en sobrecompra ({ind.rsi:.1f})",
                    "message":    f"RSI de {symbol} alcanzó {ind.rsi:.1f}, zona de sobrecompra. Posible corrección próxima.",
                    "data":       {"rsi": ind.rsi}
                })
            elif ind.rsi <= 25:
                alerts.append({
                    "symbol":     symbol,
                    "alert_type": "rsi_oversold",
                    "alert_type_label": ALERT_TYPE_LABELS["rsi_oversold"],
                    "severity":   "high" if ind.rsi <= 20 else "medium",
                    "severity_label": SEVERITY_LABELS["high" if ind.rsi <= 20 else "medium"],
                    "title":      f"{symbol} RSI en sobreventa ({ind.rsi:.1f})",
                    "message":    f"RSI de {symbol} en {ind.rsi:.1f}, zona de sobreventa extrema. Posible rebote.",
                    "data":       {"rsi": ind.rsi}
                })

        if market.volume_24h:
            recent_markets = (
                db.query(MarketData)
                .filter(MarketData.crypto_id == crypto.id)
                .order_by(MarketData.timestamp.desc())
                .limit(10)
                .all()
            )
            if len(recent_markets) >= 5:
                avg_vol = sum(m.volume_24h for m in recent_markets[1:]) / (len(recent_markets) - 1)
                if avg_vol > 0:
                    vol_change = ((market.volume_24h - avg_vol) / avg_vol) * 100
                    if vol_change > 150:
                        alerts.append({
                            "symbol":     symbol,
                            "alert_type": "volume_spike",
                            "alert_type_label": ALERT_TYPE_LABELS["volume_spike"],
                            "severity":   "critical" if vol_change > 300 else "high",
                            "severity_label": SEVERITY_LABELS["critical" if vol_change > 300 else "high"],
                            "title":      f"{symbol} spike de volumen +{vol_change:.0f}%",
                            "message":    f"Volumen inusual detectado en {symbol}: +{vol_change:.0f}% sobre el promedio. Posible movimiento institucional.",
                            "data":       {"volume_change_pct": round(vol_change, 2), "current_volume": market.volume_24h}
                        })

        try:
            structure = detect_market_structure(symbol, "1d")
            if "error" not in structure:
                support    = structure.get("current_support")
                resistance = structure.get("current_resistance")

                if support and abs((price - support) / support) < 0.02:
                    alerts.append({
                        "symbol":     symbol,
                        "alert_type": "price_at_support",
                        "alert_type_label": ALERT_TYPE_LABELS["price_at_support"],
                        "severity":   "medium",
                        "severity_label": SEVERITY_LABELS["medium"],
                        "title":      f"{symbol} tocando soporte en ${support:,.4f}",
                        "message":    f"Precio de {symbol} (${price:,.4f}) está a menos del 2% del soporte clave en ${support:,.4f}.",
                        "data":       {"price": price, "support": support}
                    })

                if resistance and abs((price - resistance) / resistance) < 0.02:
                    alerts.append({
                        "symbol":     symbol,
                        "alert_type": "price_at_resistance",
                        "alert_type_label": ALERT_TYPE_LABELS["price_at_resistance"],
                        "severity":   "medium",
                        "severity_label": SEVERITY_LABELS["medium"],
                        "title":      f"{symbol} tocando resistencia en ${resistance:,.4f}",
                        "message":    f"Precio de {symbol} (${price:,.4f}) está a menos del 2% de la resistencia en ${resistance:,.4f}.",
                        "data":       {"price": price, "resistance": resistance}
                    })

                bos = structure.get("last_bos", {})
                if bos.get("detected"):
                    direction_label = DIRECTION_LABELS.get(bos["direction"], bos["direction"])
                    alerts.append({
                        "symbol":     symbol,
                        "alert_type": "break_of_structure",
                        "alert_type_label": ALERT_TYPE_LABELS["break_of_structure"],
                        "severity":   "high",
                        "severity_label": SEVERITY_LABELS["high"],
                        "title":      f"{symbol} ruptura de estructura {direction_label}",
                        "message":    f"Se detectó un BOS {direction_label} en {symbol} en ${bos['price']:,.4f}. Posible cambio de tendencia.",
                        "data":       {**bos, "direction_label": direction_label}
                    })
        except:
            pass

        if market.change_24h:
            if abs(market.change_24h) >= 10:
                severity = "critical" if abs(market.change_24h) >= 20 else "high"
                direction = "subida" if market.change_24h > 0 else "caída"
                alerts.append({
                    "symbol":     symbol,
                    "alert_type": "extreme_price_move",
                    "alert_type_label": ALERT_TYPE_LABELS["extreme_price_move"],
                    "severity":   severity,
                    "severity_label": SEVERITY_LABELS[severity],
                    "title":      f"{symbol} {direction} extrema de {market.change_24h:.1f}% en 24h",
                    "message":    f"{symbol} registra una {direction} de {abs(market.change_24h):.1f}% en las últimas 24 horas.",
                    "data":       {"change_24h": market.change_24h, "price": price}
                })

        for alert_data in alerts:
            existing = (
                db.query(Alert)
                .filter(
                    Alert.symbol == symbol,
                    Alert.alert_type == alert_data["alert_type"],
                    Alert.triggered_at >= datetime.utcnow() - timedelta(hours=4)
                )
                .first()
            )
            if not existing:
                db.add(Alert(
                    symbol       = alert_data["symbol"],
                    alert_type   = alert_data["alert_type"],
                    severity     = alert_data["severity"],
                    title        = alert_data["title"],
                    message      = alert_data["message"],
                    data         = alert_data.get("data"),
                    triggered_at = datetime.utcnow(),
                    is_active    = 1
                ))

        db.commit()

    except Exception as e:
        print(f"Error detectando alertas para {symbol}: {e}")
        db.rollback()
    finally:
        db.close()

    return alerts

def get_all_triggered_alerts(hours: int = 24, severity: str = None) -> list:
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = (
            db.query(Alert)
            .filter(Alert.triggered_at >= since, Alert.is_active == 1)
        )
        if severity:
            query = query.filter(Alert.severity == severity)

        alerts = query.order_by(Alert.triggered_at.desc()).all()

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted([
            {
                "id":           a.id,
                "symbol":       a.symbol,
                "alert_type":   a.alert_type,
                "alert_type_label": ALERT_TYPE_LABELS.get(a.alert_type, a.alert_type),
                "severity":     a.severity,
                "severity_label": SEVERITY_LABELS.get(a.severity, a.severity),
                "title":        a.title,
                "message":      a.message,
                "data":         a.data,
                "triggered_at": a.triggered_at
            }
            for a in alerts
        ], key=lambda x: severity_order.get(x["severity"], 99))
    finally:
        db.close()
