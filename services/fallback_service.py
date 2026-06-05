from database import SessionLocal
from models import Crypto, MarketData, TechnicalIndicator, Signal, WhaleTransaction
from datetime import datetime, timedelta
from sqlalchemy import func

def _latest_market_query(db):
    subquery = (
        db.query(
            MarketData.crypto_id,
            func.max(MarketData.timestamp).label("max_ts")
        )
        .group_by(MarketData.crypto_id)
        .subquery()
    )

    return (
        db.query(MarketData, Crypto)
        .join(Crypto, MarketData.crypto_id == Crypto.id)
        .join(subquery, (MarketData.crypto_id == subquery.c.crypto_id) &
                        (MarketData.timestamp == subquery.c.max_ts))
    )

def _to_cmc_market_item(market: MarketData, crypto: Crypto) -> dict:
    return {
        "id":         crypto.cmc_id,
        "symbol":     crypto.symbol,
        "name":       crypto.name,
        "quote": {
            "USD": {
                "price":                market.price_usd,
                "market_cap":           market.market_cap,
                "volume_24h":           market.volume_24h,
                "percent_change_24h":   market.change_24h,
                "percent_change_7d":    market.change_7d,
                "volume_change_24h":    0
            }
        },
        "_source": "base_de_datos_local",
        "_timestamp": market.timestamp.isoformat() if market.timestamp else None
    }

def get_latest_market_from_db(symbol: str = None, limit: int = 50) -> list:
    db = SessionLocal()
    try:
        query = _latest_market_query(db)

        if symbol:
            query = query.filter(Crypto.symbol == symbol.upper())

        results = query.order_by(MarketData.market_cap.desc()).limit(limit).all()

        return [
            _to_cmc_market_item(market, crypto)
            for market, crypto in results
        ]
    finally:
        db.close()

def get_latest_market_by_cmc_id_from_db(cmc_id: int) -> dict | None:
    db = SessionLocal()
    try:
        result = (
            _latest_market_query(db)
            .filter(Crypto.cmc_id == cmc_id)
            .first()
        )
        if not result:
            return None
        market, crypto = result
        return _to_cmc_market_item(market, crypto)
    finally:
        db.close()

def get_latest_indicators_from_db(symbol: str) -> dict | None:
    db = SessionLocal()
    try:
        crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
        if not crypto:
            return None
        ind = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.crypto_id == crypto.id)
            .order_by(TechnicalIndicator.timestamp.desc())
            .first()
        )
        if not ind:
            return None
        return {
            "symbol":         crypto.symbol,
            "name":           crypto.name,
            "timestamp":      ind.timestamp.isoformat() if ind.timestamp else None,
            "rsi":            ind.rsi,
            "macd":           ind.macd,
            "macd_signal":    ind.macd_signal,
            "macd_histogram": ind.macd_histogram,
            "ema_9":          ind.ema_9,
            "ema_21":         ind.ema_21,
            "ema_50":         ind.ema_50,
            "adx":            ind.adx,
            "bb_upper":       ind.bb_upper,
            "bb_middle":      ind.bb_middle,
            "bb_lower":       ind.bb_lower,
            "bb_pct_b":       ind.bb_pct_b,
            "_source":        "base_de_datos_local"
        }
    finally:
        db.close()

def get_price_history_from_db(symbol: str, days: int = 60) -> list:
    db = SessionLocal()
    try:
        crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
        if not crypto:
            return []
        since = datetime.utcnow() - timedelta(days=days)
        records = (
            db.query(MarketData)
            .filter(
                MarketData.crypto_id == crypto.id,
                MarketData.timestamp >= since
            )
            .order_by(MarketData.timestamp.asc())
            .all()
        )
        return [r.price_usd for r in records if r.price_usd]
    finally:
        db.close()

def get_price_history_by_cmc_id_from_db(cmc_id: int, days: int = 60) -> list:
    db = SessionLocal()
    try:
        crypto = db.query(Crypto).filter(Crypto.cmc_id == cmc_id).first()
        if not crypto:
            return []
        since = datetime.utcnow() - timedelta(days=days)
        records = (
            db.query(MarketData)
            .filter(
                MarketData.crypto_id == crypto.id,
                MarketData.timestamp >= since
            )
            .order_by(MarketData.timestamp.asc())
            .all()
        )
        return [r.price_usd for r in records if r.price_usd]
    finally:
        db.close()

def get_ohlcv_history_from_db(symbol: str, days: int = 30) -> list:
    db = SessionLocal()
    try:
        crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
        if not crypto:
            return []
        since = datetime.utcnow() - timedelta(days=days)
        records = (
            db.query(MarketData)
            .filter(
                MarketData.crypto_id == crypto.id,
                MarketData.timestamp >= since
            )
            .order_by(MarketData.timestamp.asc())
            .all()
        )
        return [
            {
                "timestamp":  r.timestamp.isoformat() if r.timestamp else None,
                "open":       r.price_usd,
                "high":       r.price_usd,
                "low":        r.price_usd,
                "close":      r.price_usd,
                "volume":     r.volume_24h,
                "market_cap": r.market_cap,
                "_source":    "base_de_datos_local"
            }
            for r in records
            if r.price_usd
        ]
    finally:
        db.close()

def get_ohlcv_history_by_cmc_id_from_db(cmc_id: int, days: int = 30) -> list:
    db = SessionLocal()
    try:
        crypto = db.query(Crypto).filter(Crypto.cmc_id == cmc_id).first()
        if not crypto:
            return []
        return get_ohlcv_history_from_db(crypto.symbol, days=days)
    finally:
        db.close()

def _pct_change(old, new):
    if old and new and old != 0:
        return round(((new - old) / old) * 100, 2)
    return None

def get_performance_from_db(symbol: str, days: int = 31) -> dict | None:
    db = SessionLocal()
    try:
        crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
        if not crypto:
            return None
        since = datetime.utcnow() - timedelta(days=days)
        records = (
            db.query(MarketData)
            .filter(
                MarketData.crypto_id == crypto.id,
                MarketData.timestamp >= since
            )
            .order_by(MarketData.timestamp.asc())
            .all()
        )
        if not records:
            return None

        latest = records[-1]
        result = {
            "symbol": crypto.symbol,
            "name": crypto.name,
            "current_price": round(latest.price_usd, 6) if latest.price_usd else None,
            "periods": {},
            "_source": "base_de_datos_local"
        }

        if len(records) >= 2:
            previous = records[-2]
            result["periods"]["yesterday"] = {
                "open": previous.price_usd,
                "close": latest.price_usd,
                "high": max(previous.price_usd or 0, latest.price_usd or 0),
                "low": min(previous.price_usd or 0, latest.price_usd or 0),
                "percent_change": _pct_change(previous.price_usd, latest.price_usd),
                "price_change": (
                    round(latest.price_usd - previous.price_usd, 6)
                    if latest.price_usd is not None and previous.price_usd is not None
                    else None
                ),
                "open_timestamp": previous.timestamp.isoformat() if previous.timestamp else None,
                "close_timestamp": latest.timestamp.isoformat() if latest.timestamp else None
            }

        if len(records) >= 7:
            then = records[-7]
            result["periods"]["last_week"] = {
                "price_then": round(then.price_usd, 6) if then.price_usd else None,
                "price_now": round(latest.price_usd, 6) if latest.price_usd else None,
                "percent_change": _pct_change(then.price_usd, latest.price_usd),
                "date_then": then.timestamp.isoformat() if then.timestamp else None
            }

        if len(records) >= 30:
            then = records[-30]
            result["periods"]["last_month"] = {
                "price_then": round(then.price_usd, 6) if then.price_usd else None,
                "price_now": round(latest.price_usd, 6) if latest.price_usd else None,
                "percent_change": _pct_change(then.price_usd, latest.price_usd),
                "date_then": then.timestamp.isoformat() if then.timestamp else None
            }

        return result
    finally:
        db.close()

def get_trending_from_db(limit: int = 10) -> dict:
    data = get_latest_market_from_db(limit=50)
    by_change = sorted(
        data,
        key=lambda c: c.get("quote", {}).get("USD", {}).get("percent_change_24h") or 0,
        reverse=True
    )
    by_volume = sorted(
        data,
        key=lambda c: c.get("quote", {}).get("USD", {}).get("volume_24h") or 0,
        reverse=True
    )

    return {
        "trending": by_volume[:limit],
        "gainers": by_change[:limit],
        "losers": list(reversed(by_change[-limit:])),
        "most_visited": by_volume[:limit],
        "_source": "base_de_datos_local"
    }

def get_global_metrics_from_db() -> dict:
    """
    Fallback: métricas globales aproximadas calculadas desde DB.
    Se usa cuando CMC no responde para /altcoin-season y /market-regime.
    """
    db = SessionLocal()
    try:
        subquery = (
            db.query(
                MarketData.crypto_id,
                func.max(MarketData.timestamp).label("max_ts")
            )
            .group_by(MarketData.crypto_id)
            .subquery()
        )
        results = (
            db.query(MarketData, Crypto)
            .join(Crypto, MarketData.crypto_id == Crypto.id)
            .join(subquery, (MarketData.crypto_id == subquery.c.crypto_id) &
                            (MarketData.timestamp == subquery.c.max_ts))
            .all()
        )

        total_mcap   = sum(m.market_cap  or 0 for m, _ in results)
        total_vol    = sum(m.volume_24h  or 0 for m, _ in results)
        btc_mcap     = next((m.market_cap for m, c in results if c.symbol == "BTC"), 0)
        eth_mcap     = next((m.market_cap for m, c in results if c.symbol == "ETH"), 0)
        btc_dominance = (btc_mcap / total_mcap * 100) if total_mcap else 50
        eth_dominance = (eth_mcap / total_mcap * 100) if total_mcap else 15

        return {
            "btc_dominance": round(btc_dominance, 2),
            "eth_dominance": round(eth_dominance, 2),
            "quote": {
                "USD": {
                    "total_market_cap":                          total_mcap,
                    "total_volume_24h":                          total_vol,
                    "total_volume_24h_yesterday_percentage_change": 0,
                    "total_market_cap_yesterday_percentage_change": 0
                }
            },
            "_source": "base_de_datos_local"
        }
    finally:
        db.close()
