from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Crypto
from services.narrative_service import generate_narrative
from services.cache_service import get_cached, set_cache

router = APIRouter()

@router.get("/{symbol}")
def get_narrative(symbol: str, db: Session = Depends(get_db)):
    """
    Narrativa de mercado generada con IA.
    Incluye summary, bull_case, bear_case, risk_factors y market_context.
    Se cachea 30 minutos.
    """
    crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
    if not crypto:
        raise HTTPException(status_code=404, detail=f"{symbol} no encontrado")

    cache_key = f"narrative_{symbol.upper()}"
    cached = get_cached(cache_key, ttl_seconds=1800)
    if cached:
        return cached

    result = generate_narrative(symbol.upper())
    if "error" not in result:
        set_cache(cache_key, result)

    return result