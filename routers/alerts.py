from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Crypto, Alert
from services.alert_service import detect_alerts_for_symbol, get_all_triggered_alerts
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/triggered")
def get_triggered_alerts(
    hours:    int = Query(default=24, ge=1, le=168),
    severity: Optional[str] = Query(default=None, pattern="^(low|medium|high|critical)$"),
    symbol:   Optional[str] = None
):
    """
    Devuelve todas las alertas activas detectadas automáticamente.
    No requiere configuración — la API detecta condiciones notables sola.
    hours: últimas N horas (1-168)
    severity: low | medium | high | critical
    symbol: filtrar por activo
    """
    alerts = get_all_triggered_alerts(hours=hours, severity=severity)

    if symbol:
        alerts = [a for a in alerts if a["symbol"] == symbol.upper()]

    return {
        "total":     len(alerts),
        "hours":     hours,
        "severity":  severity,
        "alerts":    alerts
    }

@router.get("/scan/{symbol}")
def scan_symbol_alerts(symbol: str, db: Session = Depends(get_db)):
    """
    Escanea un activo específico ahora mismo y devuelve alertas detectadas.
    Guarda las nuevas en DB automáticamente.
    """
    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"{symbol} no encontrado")

    alerts = detect_alerts_for_symbol(symbol.upper())
    return {
        "symbol":  symbol.upper(),
        "scanned_at": datetime.utcnow().isoformat(),
        "alerts_found": len(alerts),
        "alerts": alerts
    }

@router.get("/scan/all")
def scan_all_alerts(db: Session = Depends(get_db)):
    """
    Escanea todos los activos en DB y detecta alertas.
    Útil para correr periódicamente desde el scheduler.
    """
    from models import Crypto
    cryptos = db.query(Crypto).all()
    all_alerts = []
    for crypto in cryptos:
        try:
            alerts = detect_alerts_for_symbol(crypto.symbol)
            all_alerts.extend(alerts)
        except Exception as e:
            print(f"Error escaneando {crypto.symbol}: {e}")
            continue

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_alerts.sort(key=lambda x: severity_order.get(x["severity"], 99))

    return {
        "scanned_at":    datetime.utcnow().isoformat(),
        "symbols_scanned": len(cryptos),
        "alerts_found":  len(all_alerts),
        "alerts":        all_alerts
    }