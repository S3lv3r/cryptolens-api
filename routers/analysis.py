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