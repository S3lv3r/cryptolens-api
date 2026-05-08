from fastapi import APIRouter, Query
from services.market_structure_service import detect_market_structure

router = APIRouter()

@router.get("/{symbol}")
def get_structure(
    symbol: str,
    timeframe: str = Query(default="1d", pattern="^(15m|1h|4h|1d|1w)$")
):
    """
    Análisis de estructura de mercado.
    Detecta HH/HL/LH/LL, BOS, CHOCH, soportes, resistencias y zonas de liquidez.
    timeframe: 15m | 1h | 4h | 1d | 1w
    """
    return detect_market_structure(symbol.upper(), timeframe)