from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Crypto, TechnicalAnalysisMultiTF
from services.multi_timeframe_service import analyze_timeframe, calculate_consensus
from datetime import datetime

router = APIRouter()

TIMEFRAMES = ["15m", "1h", "4h", "1d", "1w"]

@router.get("/{symbol}/multi-timeframe")
def get_multi_timeframe(symbol: str, db: Session = Depends(get_db)):
    """
    Análisis técnico completo en 5 timeframes independientes.
    Incluye consenso global y alignment score entre temporalidades.
    """
    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail=f"{symbol} no encontrado")

    analyses = {}
    for tf in TIMEFRAMES:
        result = analyze_timeframe(symbol.upper(), tf)
        analyses[tf] = result

        if result:
            record = TechnicalAnalysisMultiTF(
                symbol          = symbol.upper(),
                timeframe       = tf,
                timestamp       = datetime.utcnow(),
                rsi             = result["rsi"],
                macd            = result["macd"],
                macd_signal     = result["macd_signal"],
                macd_histogram  = result["macd_histogram"],
                ema_9           = result["ema_9"],
                ema_21          = result["ema_21"],
                ema_50          = result["ema_50"],
                ema_200         = result["ema_200"],
                adx             = result["adx"],
                bb_upper        = result["bb_upper"],
                bb_middle       = result["bb_middle"],
                bb_lower        = result["bb_lower"],
                bb_pct_b        = result["bb_pct_b"],
                atr             = result["atr"],
                trend_direction = result["trend_direction"],
                trend_strength  = result["trend_strength"],
                market_condition= result["market_condition"]
            )
            db.add(record)

    db.commit()
    consensus = calculate_consensus(analyses)

    return {
        "symbol":    symbol.upper(),
        "timestamp": datetime.utcnow().isoformat(),
        "consensus": consensus,
        "timeframes": analyses
    }