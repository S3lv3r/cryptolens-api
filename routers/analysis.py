from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import TechnicalIndicator, Crypto

router = APIRouter()

@router.get("/{symbol}")
def get_analysis(symbol: str, db: Session = Depends(get_db)):
    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail=f"{symbol} no encontrado")

    ind = (
        db.query(TechnicalIndicator)
        .filter(TechnicalIndicator.crypto_id == crypto.id)
        .order_by(TechnicalIndicator.timestamp.desc())
        .first()
    )
    if not ind:
        raise HTTPException(status_code=404, detail="No hay indicadores calculados aún")

    return {
        "symbol":    crypto.symbol,
        "name":      crypto.name,
        "timestamp": ind.timestamp,
        "trend": {
            "ema_9":    ind.ema_9,
            "ema_21":   ind.ema_21,
            "ema_50":   ind.ema_50,
            "lsma_25":  ind.lsma_25,
            "lsma_200": ind.lsma_200,
        },
        "momentum": {
            "rsi":            ind.rsi,
            "macd":           ind.macd,
            "macd_signal":    ind.macd_signal,
            "macd_histogram": ind.macd_histogram,
        },
        "volatility": {
            "bb_upper":  ind.bb_upper,
            "bb_middle": ind.bb_middle,
            "bb_lower":  ind.bb_lower,
            "bb_pct_b":  ind.bb_pct_b,
        },
        "strength": {
            "adx": ind.adx,
            "trend_strength": (
                "tendencia muy fuerte" if ind.adx >= 60 else
                "tendencia fuerte"     if ind.adx >= 40 else
                "tendencia moderada"   if ind.adx >= 20 else
                "tendencia débil o lateral"
            )
        }
    }

@router.get("/history/{symbol}")
def get_indicators_history(
    symbol: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Historial de indicadores técnicos calculados.
    Útil para graficar RSI, MACD y Bollinger en el tiempo.
    limit: número de registros históricos (default 50)
    """
    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail=f"{symbol} no encontrado")

    records = (
        db.query(TechnicalIndicator)
        .filter(TechnicalIndicator.crypto_id == crypto.id)
        .order_by(TechnicalIndicator.timestamp.desc())
        .limit(limit)
        .all()
    )

    if not records:
        raise HTTPException(status_code=404, detail="Sin historial de indicadores")

    return {
        "symbol": crypto.symbol,
        "name":   crypto.name,
        "count":  len(records),
        "data": [
            {
                "timestamp":      r.timestamp,
                "rsi":            r.rsi,
                "macd":           r.macd,
                "macd_signal":    r.macd_signal,
                "macd_histogram": r.macd_histogram,
                "bb_upper":       r.bb_upper,
                "bb_middle":      r.bb_middle,
                "bb_lower":       r.bb_lower,
                "bb_pct_b":       r.bb_pct_b,
                "ema_9":          r.ema_9,
                "ema_21":         r.ema_21,
                "adx":            r.adx
            }
            for r in reversed(records)
        ]
    }