import requests
import time
from datetime import datetime, timedelta
from config import COINMARKETCAP_API_KEY, COINMARKETCAP_BASE_URL

TRANSACTION_TYPE_LABELS = {
    "accumulation": "Acumulación",
    "exchange_deposit": "Depósito en exchange",
    "unusual_activity": "Actividad inusual"
}

def get_headers():
    return {
        "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY,
        "Accept": "application/json"
    }

def fetch_whale_events_batch() -> list:

    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/listings/latest"
    params = {
        "start":   1,
        "limit":   200,
        "convert": "USD",
        "sort":    "volume_24h",
        "sort_dir":"desc",
        "aux":     "volume_24h_reported,circulating_supply,cmc_rank"
    }
    response = requests.get(url, params=params, headers=get_headers(), timeout=15)
    response.raise_for_status()
    data = response.json()["data"]

    whale_events = []

    for item in data:
        quote          = item.get("quote", {}).get("USD", {})
        volume_change  = quote.get("volume_change_24h", 0) or 0
        volume_24h     = quote.get("volume_24h", 0) or 0
        market_cap     = quote.get("market_cap", 1) or 1
        price_change   = quote.get("percent_change_24h", 0) or 0
        symbol         = item.get("symbol", "")
        cmc_id         = item.get("id")

        if volume_change < 150:
            continue

        if volume_24h < 10_000_000:
            continue

        vol_to_mcap = (volume_24h / market_cap * 100) if market_cap else 0

        if price_change > 5 and volume_change > 150:
            tx_type = "accumulation"
            interpretation = (
                f"Spike de volumen +{volume_change:.0f}% con precio subiendo "
                f"+{price_change:.1f}%. Ratio vol/mcap: {vol_to_mcap:.1f}%. "
                f"Posible acumulación institucional o ballena comprando."
            )
        elif price_change < -5 and volume_change > 150:
            tx_type = "exchange_deposit"
            interpretation = (
                f"Spike de volumen +{volume_change:.0f}% con precio bajando "
                f"{price_change:.1f}%. Ratio vol/mcap: {vol_to_mcap:.1f}%. "
                f"Posible presión de venta masiva o depósito a exchange."
            )
        else:
            tx_type = "unusual_activity"
            interpretation = (
                f"Volumen inusual +{volume_change:.0f}% sin dirección clara de precio. "
                f"Ratio vol/mcap: {vol_to_mcap:.1f}%. Monitorear de cerca."
            )

        whale_events.append({
            "cmc_id":           cmc_id,
            "symbol":           symbol,
            "amount_usd":       volume_24h,
            "volume_change":    round(volume_change, 2),
            "price_change":     round(price_change, 2),
            "vol_to_mcap_pct":  round(vol_to_mcap, 2),
            "from_wallet":      "volume_spike_detected",
            "to_wallet":        "volume_spike_detected",
            "transaction_type": tx_type,
            "transaction_type_label": TRANSACTION_TYPE_LABELS.get(tx_type, tx_type),
            "interpretation":   interpretation,
            "timestamp":        datetime.utcnow().isoformat()
        })

    whale_events.sort(key=lambda x: x["amount_usd"], reverse=True)
    print(f"🐋 {len(whale_events)} eventos de ballenas detectados")
    return whale_events

def interpret_whale_transaction(tx: dict) -> str:
    return tx.get("interpretation", "Sin interpretación disponible")
