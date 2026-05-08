from services.market_service import fetch_global_metrics, fetch_top_cryptos
from services.binance_service import fetch_klines
from services.technical_service import calculate_rsi

def calculate_aggregate_rsi(top_cryptos: list) -> float:
    changes = [
        c["quote"]["USD"].get("percent_change_7d", 0) or 0
        for c in top_cryptos[:20]
    ]
    avg_change = sum(changes) / len(changes) if changes else 0
    rsi_approx = 50 + (avg_change * 2)
    return round(max(0, min(100, rsi_approx)), 2)

def detect_market_regime() -> dict:

    try:
        metrics     = fetch_global_metrics()
        top_cryptos = fetch_top_cryptos(limit=50)
    except Exception as e:
        return {"error": str(e)}

    quote           = metrics.get("quote", {}).get("USD", {})
    btc_dominance   = metrics.get("btc_dominance", 50)
    total_mcap      = quote.get("total_market_cap", 0)
    total_vol       = quote.get("total_volume_24h", 0)
    vol_change      = quote.get("total_volume_24h_yesterday_percentage_change", 0) or 0
    mcap_change     = quote.get("total_market_cap_yesterday_percentage_change", 0) or 0

    btc_klines = fetch_klines("BTC", "1d", limit=50)
    btc_closes = [k["close"] for k in btc_klines]
    btc_rsi    = calculate_rsi(btc_closes) if len(btc_closes) >= 14 else 50

    agg_rsi = calculate_aggregate_rsi(top_cryptos)

    advancing = sum(
        1 for c in top_cryptos
        if (c["quote"]["USD"].get("percent_change_24h") or 0) > 0
    )
    declining = len(top_cryptos) - advancing
    breadth   = advancing / len(top_cryptos) if top_cryptos else 0.5

    if btc_rsi > 80 and breadth > 0.8 and vol_change > 50:
        regime      = "euphoric"
        description = "Mercado en euforia. RSI extremo, volumen expansivo y amplitud máxima. Alto riesgo de corrección."
        confidence  = 0.85
    elif btc_rsi < 25 and breadth < 0.2 and mcap_change < -5:
        regime      = "panic"
        description = "Mercado en pánico. Ventas masivas generalizadas. Posible oportunidad de acumulación."
        confidence  = 0.85
    elif btc_dominance > 55 and breadth < 0.4 and vol_change < 0:
        regime      = "distribution"
        description = "Distribución activa. Capital rotando hacia BTC o saliendo del mercado."
        confidence  = 0.75
    elif btc_dominance < 45 and breadth > 0.65 and agg_rsi > 55:
        regime      = "accumulation"
        description = "Acumulación detectada. Capital entrando al mercado con preferencia por altcoins."
        confidence  = 0.75
    elif vol_change > 30 and abs(mcap_change) > 3:
        regime      = "trending"
        description = "Mercado en tendencia con expansión de volumen. Momentum direccional activo."
        confidence  = 0.70
    else:
        regime      = "ranging"
        description = "Mercado lateral. Sin tendencia clara, volumen bajo y dirección indefinida."
        confidence  = 0.65

    return {
        "regime":          regime,
        "confidence":      confidence,
        "description":     description,
        "metrics": {
            "btc_dominance":  round(btc_dominance, 2),
            "btc_rsi":        btc_rsi,
            "aggregate_rsi":  agg_rsi,
            "breadth":        round(breadth, 3),
            "advancing":      advancing,
            "declining":      declining,
            "vol_change_24h": round(vol_change, 2),
            "mcap_change_24h":round(mcap_change, 2),
            "total_market_cap":total_mcap,
            "total_volume_24h":total_vol
        }
    }