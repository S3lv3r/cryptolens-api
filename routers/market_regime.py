from fastapi import APIRouter
from services.market_regime_service import detect_market_regime
from services.cache_service import get_cached, set_cache

router = APIRouter()

@router.get("/")
def get_market_regime():
    """
    Clasificación del estado global del mercado.
    Estados: trending | ranging | euphoric | panic | accumulation | distribution
    Se cachea 15 minutos.
    """
    cached = get_cached("market_regime", ttl_seconds=900)
    if cached:
        return cached

    result = detect_market_regime()
    set_cache("market_regime", result)
    return result