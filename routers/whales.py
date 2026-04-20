from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import WhaleTransaction, Crypto
from services.whale_service import fetch_whale_events_batch
from typing import Optional

router = APIRouter()

@router.get("/")
def get_whales(
    symbol: Optional[str] = None,
    limit: int = 50,
    source: str = "db",
    db: Session = Depends(get_db)
):
    if source == "live":
        events = fetch_whale_events_batch()
        if symbol:
            events = [e for e in events if e["symbol"] == symbol.upper()]
        return events[:limit]

    query = (
        db.query(WhaleTransaction, Crypto)
        .join(Crypto, WhaleTransaction.crypto_id == Crypto.id)
    )
    if symbol:
        query = query.filter(Crypto.symbol == symbol.upper())

    results = query.order_by(WhaleTransaction.timestamp.desc()).limit(limit).all()

    if not results:
        return {
            "message": "No hay eventos en DB aún. Usa ?source=live para consultar en tiempo real o espera el scheduler.",
            "tip": "GET /whales?source=live"
        }

    return [
        {
            "symbol":           crypto.symbol,
            "amount_usd":       tx.amount_usd,
            "transaction_type": tx.transaction_type,
            "interpretation":   tx.interpretation,
            "timestamp":        tx.timestamp
        }
        for tx, crypto in results
    ]