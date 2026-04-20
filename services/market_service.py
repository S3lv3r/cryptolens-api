import requests
import time
from config import COINMARKETCAP_API_KEY, COINMARKETCAP_BASE_URL

def get_headers():
    return {
        "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY,
        "Accept": "application/json"
    }

def fetch_top_cryptos(limit: int = 50) -> list:
    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/listings/latest"
    params = {
        "start": 1,
        "limit": limit,
        "convert": "USD",
        "sort": "market_cap",
        "sort_dir": "desc",
        "aux": "volume_24h_reported,circulating_supply,total_supply,max_supply,cmc_rank,num_market_pairs"
    }
    response = requests.get(url, params=params, headers=get_headers(), timeout=10)
    response.raise_for_status()
    return response.json()["data"]

def fetch_price_history(cmc_id: int, days: int = 60) -> list:
    from datetime import datetime, timedelta
    import time

    time_end   = datetime.utcnow()
    time_start = time_end - timedelta(days=days)

    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/quotes/historical"
    params = {
        "id":         cmc_id,
        "time_start": time_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "time_end":   time_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interval":   "daily",
        "convert":    "USD",
        "count":      days
    }

    time.sleep(2)

    response = requests.get(url, params=params, headers=get_headers(), timeout=15)
    response.raise_for_status()
    data = response.json()
    quotes = data["data"]["quotes"]
    return [q["quote"]["USD"]["price"] for q in quotes]

def fetch_ohlcv_history(cmc_id: int, days: int = 30) -> list:
    from datetime import datetime, timedelta
    time_end   = datetime.utcnow()
    time_start = time_end - timedelta(days=days)

    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/ohlcv/historical"
    params = {
        "id":         cmc_id,
        "time_start": time_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "time_end":   time_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interval":   "daily",
        "convert":    "USD"
    }
    response = requests.get(url, params=params, headers=get_headers(), timeout=15)
    response.raise_for_status()
    data = response.json()
    quotes = data["data"]["quotes"]
    return [
        {
            "open":   q["quote"]["USD"]["open"],
            "high":   q["quote"]["USD"]["high"],
            "low":    q["quote"]["USD"]["low"],
            "close":  q["quote"]["USD"]["close"],
            "volume": q["quote"]["USD"]["volume"]
        }
        for q in quotes
    ]

def fetch_price_performance(cmc_id: int) -> dict:
    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/price-performance-stats/latest"
    params = {
        "id":          cmc_id,
        "convert":     "USD",
        "time_period": "yesterday,last_week,last_month,last_quarter"
    }
    response = requests.get(url, params=params, headers=get_headers(), timeout=10)
    response.raise_for_status()
    data = response.json()["data"]

    crypto_data = list(data.values())[0] if data else {}
    periods = crypto_data.get("periods", {})

    return {
        "symbol":   crypto_data.get("symbol", ""),
        "name":     crypto_data.get("name", ""),
        "periods": {
            "yesterday": {
                "open":           periods.get("yesterday", {}).get("open", {}).get("USD", None),
                "close":          periods.get("yesterday", {}).get("close", {}).get("USD", None),
                "percent_change": periods.get("yesterday", {}).get("percent_change", {}).get("USD", None),
                "high":           periods.get("yesterday", {}).get("high", {}).get("USD", None),
                "low":            periods.get("yesterday", {}).get("low", {}).get("USD", None),
            },
            "last_week": {
                "open":           periods.get("last_week", {}).get("open", {}).get("USD", None),
                "close":          periods.get("last_week", {}).get("close", {}).get("USD", None),
                "percent_change": periods.get("last_week", {}).get("percent_change", {}).get("USD", None),
                "high":           periods.get("last_week", {}).get("high", {}).get("USD", None),
                "low":            periods.get("last_week", {}).get("low", {}).get("USD", None),
            },
            "last_month": {
                "open":           periods.get("last_month", {}).get("open", {}).get("USD", None),
                "close":          periods.get("last_month", {}).get("close", {}).get("USD", None),
                "percent_change": periods.get("last_month", {}).get("percent_change", {}).get("USD", None),
                "high":           periods.get("last_month", {}).get("high", {}).get("USD", None),
                "low":            periods.get("last_month", {}).get("low", {}).get("USD", None),
            },
            "last_quarter": {
                "open":           periods.get("last_quarter", {}).get("open", {}).get("USD", None),
                "close":          periods.get("last_quarter", {}).get("close", {}).get("USD", None),
                "percent_change": periods.get("last_quarter", {}).get("percent_change", {}).get("USD", None),
                "high":           periods.get("last_quarter", {}).get("high", {}).get("USD", None),
                "low":            periods.get("last_quarter", {}).get("low", {}).get("USD", None),
            }
        }
    }

def fetch_trending_latest() -> dict:
    results = {}

    try:
        url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/trending/latest"
        r = requests.get(url, headers=get_headers(), timeout=10)
        if r.ok:
            results["trending"] = r.json().get("data", [])
        else:
            results["trending"] = []
    except Exception as e:
        results["trending"] = []
        print(f"X trending/latest: {e}")

    time.sleep(0.5)

    try:
        url2 = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/trending/gainers-losers"
        r2 = requests.get(url2, params={"limit": 10, "convert": "USD", "time_period": "24h"}, headers=get_headers(), timeout=10)
        if r2.ok:
            data2 = r2.json().get("data", [])
            if isinstance(data2, dict):
                results["gainers"] = data2.get("gainers", [])
                results["losers"]  = data2.get("losers", [])
            elif isinstance(data2, list):
                results["gainers"] = sorted(
                    [c for c in data2 if c.get("quote", {}).get("USD", {}).get("percent_change_24h", 0) > 0],
                    key=lambda x: x["quote"]["USD"]["percent_change_24h"],
                    reverse=True
                )[:10]
                results["losers"] = sorted(
                    [c for c in data2 if c.get("quote", {}).get("USD", {}).get("percent_change_24h", 0) < 0],
                    key=lambda x: x["quote"]["USD"]["percent_change_24h"]
                )[:10]
        else:
            results["gainers"] = []
            results["losers"]  = []
    except Exception as e:
        results["gainers"] = []
        results["losers"]  = []
        print(f"X  trending/gainers-losers: {e}")

    time.sleep(0.5)
    try:
        url3 = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/trending/most-visited"
        r3 = requests.get(url3, params={"limit": 10, "convert": "USD"}, headers=get_headers(), timeout=10)
        if r3.ok:
            results["most_visited"] = r3.json().get("data", [])
        else:
            results["most_visited"] = []
    except Exception as e:
        results["most_visited"] = []
        print(f"X  trending/most-visited: {e}")

    return results

def fetch_global_metrics() -> dict:
    url = f"{COINMARKETCAP_BASE_URL}/global-metrics/quotes/latest"
    response = requests.get(url, headers=get_headers(), timeout=10)
    response.raise_for_status()
    return response.json()["data"]

def fetch_crypto_metadata(cmc_ids: list) -> dict:
    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/info"
    params = {"id": ",".join(str(i) for i in cmc_ids)}
    response = requests.get(url, params=params, headers=get_headers(), timeout=15)
    response.raise_for_status()
    return response.json()["data"]

def fetch_market_pairs(cmc_id: int, limit: int = 10) -> list:
    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/market-pairs/latest"
    params = {
        "id":      cmc_id,
        "limit":   limit,
        "convert": "USD"
    }
    response = requests.get(url, params=params, headers=get_headers(), timeout=10)
    response.raise_for_status()
    return response.json()["data"].get("market_pairs", [])

def fetch_crypto_categories() -> list:
    url = f"{COINMARKETCAP_BASE_URL}/cryptocurrency/categories"
    params = {"limit": 20, "convert": "USD"}
    response = requests.get(url, params=params, headers=get_headers(), timeout=10)
    response.raise_for_status()
    return response.json()["data"]

def fetch_news() -> list:
    import xml.etree.ElementTree as ET

    url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    channel = root.find("channel")
    items = channel.findall("item")

    news = []
    for item in items[:20]:
        news.append({
            "title":       item.findtext("title", ""),
            "link":        item.findtext("link", ""),
            "description": item.findtext("description", ""),
            "published":   item.findtext("pubDate", ""),
            "source":      "CoinDesk"
        })
    return news

def detect_volume_spike(item: dict) -> dict | None:
    quote = item.get("quote", {}).get("USD", {})
    volume_change = quote.get("volume_change_24h", 0) or 0
    volume_24h    = quote.get("volume_24h", 0) or 0
    market_cap    = quote.get("market_cap", 1) or 1
    price_change  = quote.get("percent_change_24h", 0) or 0
    symbol        = item.get("symbol", "")

    if volume_change < 150:
        return None

    vol_to_mcap = (volume_24h / market_cap) * 100

    if price_change > 5 and volume_change > 150:
        tx_type      = "accumulation"
        interpretation = (
            f"Spike de volumen +{volume_change:.0f}% con precio subiendo +{price_change:.1f}%. "
            f"Posible acumulación institucional o ballena comprando."
        )
    elif price_change < -5 and volume_change > 150:
        tx_type      = "exchange_deposit"
        interpretation = (
            f"Spike de volumen +{volume_change:.0f}% con precio bajando {price_change:.1f}%. "
            f"Posible presión de venta masiva o ballena moviendo a exchange."
        )
    else:
        tx_type      = "unusual_activity"
        interpretation = (
            f"Volumen inusual +{volume_change:.0f}% sin movimiento de precio claro. "
            f"Ratio vol/mcap: {vol_to_mcap:.1f}%. Monitorear de cerca."
        )

    return {
        "symbol":         symbol,
        "volume_change":  round(volume_change, 2),
        "price_change":   round(price_change, 2),
        "volume_24h":     volume_24h,
        "vol_to_mcap_pct": round(vol_to_mcap, 2),
        "transaction_type": tx_type,
        "interpretation": interpretation
    }
