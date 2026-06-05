import requests
from datetime import datetime

BINANCE_BASE_URL = "https://api.binance.com/api/v3"
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1"

# Mapeo de intervalos
TIMEFRAME_MAP = {
    "15m": "15m",
    "1h":  "1h",
    "4h":  "4h",
    "1d":  "1d",
    "1w":  "1w"
}

def get_binance_symbol(symbol: str) -> str:
    stablecoins = {"USDT", "USDC", "DAI", "BUSD"}
    if symbol.upper() in stablecoins:
        return None
    return f"{symbol.upper()}USDT"

def fetch_klines(symbol: str, timeframe: str, limit: int = 200) -> list:

    pair = get_binance_symbol(symbol)
    if not pair:
        return []

    interval = TIMEFRAME_MAP.get(timeframe, "1d")
    url = f"{BINANCE_BASE_URL}/klines"
    params = {
        "symbol":   pair,
        "interval": interval,
        "limit":    limit
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        raw = r.json()

        return [
            {
                "timestamp": datetime.utcfromtimestamp(c[0] / 1000).isoformat(),
                "open":      float(c[1]),
                "high":      float(c[2]),
                "low":       float(c[3]),
                "close":     float(c[4]),
                "volume":    float(c[5])
            }
            for c in raw
        ]
    except Exception as e:
        print(f" Binance klines {symbol} {timeframe}: {e}")
        return []

def fetch_funding_rate(symbol: str) -> dict:
    pair = get_binance_symbol(symbol)
    if not pair:
        return {}
    try:
        url = f"{BINANCE_FUTURES_URL}/fundingRate"
        r = requests.get(url, params={"symbol": pair, "limit": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            return {
                "symbol":       symbol,
                "funding_rate": float(data[0]["fundingRate"]),
                "funding_time": data[0]["fundingTime"]
            }
    except Exception as e:
        print(f" Funding rate {symbol}: {e}")
    return {}

def fetch_open_interest(symbol: str) -> dict:
    pair = get_binance_symbol(symbol)
    if not pair:
        return {}
    try:
        url = f"{BINANCE_FUTURES_URL}/openInterest"
        r = requests.get(url, params={"symbol": pair}, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "symbol":        symbol,
            "open_interest": float(data["openInterest"]),
            "timestamp":     data["time"]
        }
    except Exception as e:
        print(f" Open interest {symbol}: {e}")
    return {}

def fetch_long_short_ratio(symbol: str) -> dict:
    pair = get_binance_symbol(symbol)
    if not pair:
        return {}
    try:
        url = f"{BINANCE_FUTURES_URL}/globalLongShortAccountRatio"
        r = requests.get(url, params={"symbol": pair, "period": "1h", "limit": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            return {
                "symbol":      symbol,
                "long_ratio":  float(data[0]["longAccount"]),
                "short_ratio": float(data[0]["shortAccount"]),
                "timestamp":   data[0]["timestamp"]
            }
    except Exception as e:
        print(f" Long/short ratio {symbol}: {e}")
    return {}

def fetch_order_book_depth(symbol: str, limit: int = 20) -> dict:
    pair = get_binance_symbol(symbol)
    if not pair:
        return {}
    try:
        url = f"{BINANCE_BASE_URL}/depth"
        r = requests.get(url, params={"symbol": pair, "limit": limit}, timeout=10)
        r.raise_for_status()
        data = r.json()

        bids = [[float(p), float(q)] for p, q in data["bids"]]
        asks = [[float(p), float(q)] for p, q in data["asks"]]

        total_bid_volume = sum(q for _, q in bids)
        total_ask_volume = sum(q for _, q in asks)
        pressure = "buy" if total_bid_volume > total_ask_volume else "sell"

        return {
            "symbol":           symbol,
            "best_bid":         bids[0][0] if bids else None,
            "best_ask":         asks[0][0] if asks else None,
            "bid_volume":       round(total_bid_volume, 4),
            "ask_volume":       round(total_ask_volume, 4),
            "pressure":         pressure,
            "pressure_label":   "Compra" if pressure == "buy" else "Venta",
            "top_bids":         bids[:5],
            "top_asks":         asks[:5]
        }
    except Exception as e:
        print(f" Order book {symbol}: {e}")
    return {}
