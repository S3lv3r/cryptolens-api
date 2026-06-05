from services.market_service import fetch_global_metrics

def calculate_altcoin_season_index(top20_data: list) -> dict:
    metrics = fetch_global_metrics()
    btc_dominance = metrics["btc_dominance"]
    eth_dominance = metrics["eth_dominance"]
    total_market_cap = metrics["quote"]["USD"]["total_market_cap"]
    total_volume_24h = metrics["quote"]["USD"]["total_volume_24h"]

    btc_data = next((c for c in top20_data if c["symbol"] == "BTC"), None)
    btc_7d = btc_data["quote"]["USD"].get("percent_change_7d", 0) if btc_data else 0

    altcoins = [c for c in top20_data if c["symbol"] not in ("BTC", "USDT", "USDC", "DAI")]
    outperforming = sum(
        1 for c in altcoins
        if c["quote"]["USD"].get("percent_change_7d", 0) > btc_7d
    )
    total_altcoins = len(altcoins)
    outperform_pct = (outperforming / total_altcoins * 100) if total_altcoins > 0 else 0

    if btc_dominance > 55 and outperform_pct < 25:
        season = "Bitcoin Season"
        season_label = "Temporada de Bitcoin"
        description = "El capital se concentra en Bitcoin. Las altcoins están rezagadas."
        score = round(outperform_pct)
    elif outperform_pct >= 75 and btc_dominance < 45:
        season = "Altcoin Season"
        season_label = "Temporada de altcoins"
        description = "Las altcoins están superando a Bitcoin. El capital fluye hacia el mercado alternativo."
        score = round(outperform_pct)
    else:
        season = "Zona Neutral"
        season_label = "Zona neutral"
        description = "Mercado indeciso. Mezcla de fuerza entre Bitcoin y altcoins."
        score = round(outperform_pct)

    return {
        "season": season,
        "season_label": season_label,
        "score": score,
        "description": description,
        "btc_dominance": round(btc_dominance, 2),
        "eth_dominance": round(eth_dominance, 2),
        "altcoins_outperforming_btc": outperforming,
        "total_altcoins_analyzed": total_altcoins,
        "btc_7d_change": round(btc_7d, 2),
        "total_market_cap_usd": total_market_cap,
        "total_volume_24h_usd": total_volume_24h,
        "_source": metrics.get("_source", "coinmarketcap")
    }
