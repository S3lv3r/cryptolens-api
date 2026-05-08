from fastapi import APIRouter, Query
from services.volatility_service import analyze_volatility

router = APIRouter()

@router.get("/{symbol}")
def get_volatility(
    symbol: str,
    timeframe: str = Query(default="1d", pattern="^(15m|1h|4h|1d|1w)$")
):
    """
    Análisis de volatilidad contextual.
    Incluye ATR, volatilidad histórica, percentil y régimen de volatilidad.
    """
    return analyze_volatility(symbol.upper(), timeframe)