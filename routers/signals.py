from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Signal, Crypto, TechnicalIndicator, MarketData
from sqlalchemy import func

router = APIRouter()

@router.get("/{symbol}")
def get_signal(symbol: str, db: Session = Depends(get_db)):
    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail=f"Criptomoneda '{symbol}' no encontrada")

    signal = (
        db.query(Signal)
        .filter(Signal.crypto_id == crypto.id)
        .order_by(Signal.timestamp.desc())
        .first()
    )
    if not signal:
        raise HTTPException(status_code=404, detail="No hay señales calculadas aún para este activo")

    market = (
        db.query(MarketData)
        .filter(MarketData.crypto_id == crypto.id)
        .order_by(MarketData.timestamp.desc())
        .first()
    )

    ind = (
        db.query(TechnicalIndicator)
        .filter(TechnicalIndicator.crypto_id == crypto.id)
        .order_by(TechnicalIndicator.timestamp.desc())
        .first()
    )

    return {
        "symbol":      crypto.symbol,
        "name":        crypto.name,
        "timestamp":   signal.timestamp,

        "market": {
            "price_usd":  market.price_usd  if market else None,
            "change_24h": market.change_24h if market else None,
            "volume_24h": market.volume_24h if market else None,
        },

        "recommendation": {
            "action":      signal.action,
            "confidence":  signal.confidence,
            "explanation": signal.explanation,
            "whale_alert": signal.whale_activity
        },

        "horizons": {
            "short_term": {
                "label":  "Corto plazo (1-7 días)",
                "action": signal.short_term_action,
                "risk":   signal.short_term_risk,
                "notes":  signal.short_term_notes
            },
            "medium_term": {
                "label":  "Mediano plazo (1-3 meses)",
                "action": signal.medium_term_action,
                "notes":  signal.medium_term_notes
            },
            "long_term": {
                "label":  "Largo plazo (+6 meses)",
                "action": signal.long_term_action,
                "notes":  signal.long_term_notes
            }
        },

        "indicators": {
            "rsi":      ind.rsi      if ind else None,
            "macd":     ind.macd     if ind else None,
            "adx":      ind.adx      if ind else None,
            "bb_pct_b": ind.bb_pct_b if ind else None,
            "ema_9":    ind.ema_9    if ind else None,
            "ema_21":   ind.ema_21   if ind else None,
            "lsma_25":  ind.lsma_25  if ind else None,
        }
    }