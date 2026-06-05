from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import MarketData, Crypto, Signal
from schemas import RankingItem
from typing import List

router = APIRouter()

ACTION_LABELS = {
    "BUY": "Comprar",
    "SELL": "Vender",
    "HOLD": "Esperar"
}

@router.get("/", response_model=List[RankingItem])
def get_ranking(db: Session = Depends(get_db)):

    cryptos = db.query(Crypto).all()
    ranking = []

    for i, crypto in enumerate(cryptos, start=1):
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
        if market:
            ranking.append(RankingItem(
                rank=i,
                symbol=crypto.symbol,
                name=crypto.name,
                price_usd=market.price_usd,
                market_cap=market.market_cap,
                change_24h=market.change_24h,
                signal=signal.action if signal else None,
                signal_label=ACTION_LABELS.get(signal.action, signal.action) if signal else None
            ))

    ranking.sort(key=lambda x: x.market_cap, reverse=True)
    for i, item in enumerate(ranking, start=1):
        item.rank = i

    return ranking
