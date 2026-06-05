from fastapi import APIRouter
from services.binance_service import (
    fetch_funding_rate,
    fetch_open_interest,
    fetch_long_short_ratio,
    fetch_order_book_depth
)

router = APIRouter()

@router.get("/{symbol}")
def get_derivatives(symbol: str):
    """
    Datos de mercado de derivados desde Binance Futures.
    Incluye tasa de funding, interés abierto, ratio largo/corto y libro de órdenes.
    """
    return {
        "symbol":          symbol.upper(),
        "funding_rate":    fetch_funding_rate(symbol.upper()),
        "open_interest":   fetch_open_interest(symbol.upper()),
        "long_short_ratio":fetch_long_short_ratio(symbol.upper()),
        "order_book":      fetch_order_book_depth(symbol.upper())
    }
