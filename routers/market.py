from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import MarketData, Crypto
from schemas import MarketDataOut
from typing import List

router = APIRouter()

@router.get("/history/{symbol}")
def get_price_history(
    symbol: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):

    from datetime import datetime, timedelta

    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail=f"{symbol} no encontrado")

    since = datetime.utcnow() - timedelta(hours=hours)

    records = (
        db.query(MarketData)
        .filter(
            MarketData.crypto_id == crypto.id,
            MarketData.timestamp >= since
        )
        .order_by(MarketData.timestamp.asc())
        .all()
    )

    return {
        "symbol": crypto.symbol,
        "name":   crypto.name,
        "hours":  hours,
        "count":  len(records),
        "data": [
            {
                "timestamp":  r.timestamp,
                "price_usd":  r.price_usd,
                "volume_24h": r.volume_24h,
                "market_cap": r.market_cap,
                "change_24h": r.change_24h
            }
            for r in records
        ]
    }

@router.get("/top50", response_model=List[MarketDataOut])
def get_top50(db: Session = Depends(get_db)):
    subquery = (
        db.query(
            MarketData.crypto_id,
            func.max(MarketData.timestamp).label("max_ts")
        )
        .group_by(MarketData.crypto_id)
        .subquery()
    )

    results = (
        db.query(MarketData, Crypto)
        .join(Crypto, MarketData.crypto_id == Crypto.id)
        .join(subquery, (MarketData.crypto_id == subquery.c.crypto_id) &
                        (MarketData.timestamp == subquery.c.max_ts))
        .order_by(MarketData.market_cap.desc())
        .limit(50)
        .all()
    )

    return [
        MarketDataOut(
            symbol=crypto.symbol,
            name=crypto.name,
            price_usd=market.price_usd,
            market_cap=market.market_cap,
            volume_24h=market.volume_24h,
            change_24h=market.change_24h,
            change_7d=market.change_7d,
            timestamp=market.timestamp
        )
        for market, crypto in results
    ]



    # No BORRAR
    results = (
        db.query(MarketData, Crypto)
        .join(Crypto, MarketData.crypto_id == Crypto.id)
        .join(subquery, (MarketData.crypto_id == subquery.c.crypto_id) &
                        (MarketData.timestamp == subquery.c.max_ts))
        .order_by(MarketData.market_cap.desc())
        .limit(20)
        .all()
    )

    return [
        MarketDataOut(
            symbol=crypto.symbol,
            name=crypto.name,
            price_usd=market.price_usd,
            market_cap=market.market_cap,
            volume_24h=market.volume_24h,
            change_24h=market.change_24h,
            change_7d=market.change_7d,
            timestamp=market.timestamp
        )
        for market, crypto in results
    ]