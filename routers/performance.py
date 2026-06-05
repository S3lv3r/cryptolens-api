from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Crypto
from services.market_service import get_headers, COINMARKETCAP_BASE_URL
from services.fallback_service import get_performance_from_db
from datetime import datetime, timedelta
import requests

router = APIRouter()

def pct_change(old, new):
    if old and new and old != 0:
        return round(((new - old) / old) * 100, 2)
    return None

@router.get("/{symbol}")
def get_performance(symbol: str, db: Session = Depends(get_db)):
    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail=f"{symbol} no encontrado")

    result = {
        "symbol": crypto.symbol,
        "name":   crypto.name,
        "periods": {}
    }

    try:
        url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/price-performance-stats/latest"
        r = requests.get(
            url,
            params={"id": crypto.cmc_id, "convert": "USD", "time_period": "yesterday"},
            headers=get_headers(),
            timeout=10
        )
        if r.ok:
            raw     = r.json()["data"][str(crypto.cmc_id)]
            period  = raw["periods"]["yesterday"]
            quote   = period["quote"]["USD"]
            result["periods"]["yesterday"] = {
                "open":           round(quote["open"], 6),
                "close":          round(quote["close"], 6),
                "high":           round(quote["high"], 6),
                "low":            round(quote["low"], 6),
                "percent_change": round(quote["percent_change"], 4),
                "price_change":   round(quote["price_change"], 6),
                "open_timestamp": period["open_timestamp"],
                "close_timestamp": period["close_timestamp"]
            }
    except Exception:
        result["periods"]["yesterday"] = {"error": "No se pudo consultar CoinMarketCap"}

    try:
        now        = datetime.utcnow()
        time_start = now - timedelta(days=31)

        url2 = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/quotes/historical"
        r2 = requests.get(
            url2,
            params={
                "id": crypto.cmc_id,
                "time_start": time_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "time_end": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "interval": "daily",
                "convert": "USD",
                "count":32
            },
            headers=get_headers(),
            timeout=15
        )

        if r2.ok:
            quotes = r2.json()["data"]["quotes"]

            current_price = quotes[-1]["quote"]["USD"]["price"]
            result["current_price"] = round(current_price, 6)

            if len(quotes) >= 7:
                price_7d = quotes[-7]["quote"]["USD"]["price"]
                result["periods"]["last_week"] = {
                    "price_then":     round(price_7d, 6),
                    "price_now":      round(current_price, 6),
                    "percent_change": pct_change(price_7d, current_price),
                    "date_then":      quotes[-7]["timestamp"]
                }

            if len(quotes) >= 30:
                price_30d = quotes[-30]["quote"]["USD"]["price"]
                result["periods"]["last_month"] = {
                    "price_then":     round(price_30d, 6),
                    "price_now":      round(current_price, 6),
                    "percent_change": pct_change(price_30d, current_price),
                    "date_then":      quotes[-30]["timestamp"]
                }

    except Exception:
        result["periods"]["last_week"]  = {"error": "No se pudo consultar CoinMarketCap"}
        result["periods"]["last_month"] = {"error": "No se pudo consultar CoinMarketCap"}

    if not result["periods"] or any("error" in period for period in result["periods"].values()):
        fallback = get_performance_from_db(symbol.upper())
        if fallback:
            return fallback

    return result
