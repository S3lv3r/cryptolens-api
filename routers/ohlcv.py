from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Crypto
from services.market_service import get_headers, COINMARKETCAP_BASE_URL
from datetime import datetime, timedelta
import requests

router = APIRouter()

@router.get("/{symbol}")
def get_ohlcv(
    symbol: str,
    days: int = Query(default=30, ge=1, le=60),
    db: Session = Depends(get_db)
):
    """
    Datos OHLCV diarios para gráficas de velas japonesas.
    days: número de días hacia atrás (1-60)
    Ejemplo: /ohlcv/BTC?days=30
    """
    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail=f"{symbol} no encontrado")

    now        = datetime.utcnow()
    time_start = now - timedelta(days=days)

    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/ohlcv/historical"
    r = requests.get(
        url,
        params={
            "id":         crypto.cmc_id,
            "time_start": time_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "time_end":   now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "interval":   "daily",
            "convert":    "USD"
        },
        headers=get_headers(),
        timeout=15
    )

    if not r.ok:
        raise HTTPException(status_code=r.status_code, detail="Error al obtener datos de CMC")

    quotes = r.json()["data"]["quotes"]

    return {
        "symbol": crypto.symbol,
        "name":   crypto.name,
        "days":   days,
        "count":  len(quotes),
        "data": [
            {
                "timestamp":  q["time_open"],
                "open":       round(q["quote"]["USD"]["open"],       6),
                "high":       round(q["quote"]["USD"]["high"],       6),
                "low":        round(q["quote"]["USD"]["low"],        6),
                "close":      round(q["quote"]["USD"]["close"],      6),
                "volume":     round(q["quote"]["USD"]["volume"],     2),
                "market_cap": round(q["quote"]["USD"]["market_cap"], 2)
            }
            for q in quotes
        ]
    }