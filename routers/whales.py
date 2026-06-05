from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import WhaleTransaction, Crypto
from services.whale_service import fetch_whale_events_batch
from typing import Optional

router = APIRouter()

TRANSACTION_TYPE_LABELS = {
    "accumulation": "Acumulación",
    "exchange_deposit": "Depósito en exchange",
    "unusual_activity": "Actividad inusual"
}

@router.get("/")
def get_whales(
    symbol: Optional[str] = None,
    limit: int = 50,
    source: str = "db",
    db: Session = Depends(get_db)
):
    if source == "live":
        try:
            events = fetch_whale_events_batch()
            if symbol:
                events = [e for e in events if e["symbol"] == symbol.upper()]
            return events[:limit]
        except Exception:
            source = "db"

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
            "transaction_type_label": TRANSACTION_TYPE_LABELS.get(tx.transaction_type, tx.transaction_type),
            "interpretation":   tx.interpretation,
            "timestamp":        tx.timestamp
        }
        for tx, crypto in results
    ]
