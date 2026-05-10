import requests
import json
from datetime import datetime
from config import GROQ_API_KEY, GROQ_MODEL
from services.market_service import fetch_global_metrics, fetch_top_cryptos
from services.market_regime_service import detect_market_regime
from services.cache_service import get_cached, set_cache
from database import SessionLocal
from models import Alert, Signal, Crypto, MarketData

def build_briefing_context(context_type: str) -> str:
    """Construye el contexto completo del mercado para el briefing."""
    parts = []

    try:
        metrics = fetch_global_metrics()
        quote   = metrics.get("quote", {}).get("USD", {})
        parts.append(
            f"MERCADO GLOBAL: Cap total ${quote.get('total_market_cap', 0):,.0f} | "
            f"Vol 24h ${quote.get('total_volume_24h', 0):,.0f} | "
            f"BTC dominancia {metrics.get('btc_dominance', 0):.1f}% | "
            f"ETH dominancia {metrics.get('eth_dominance', 0):.1f}%"
        )
    except:
        pass

    try:
        regime = detect_market_regime()
        parts.append(
            f"RÉGIMEN: {regime.get('regime', 'unknown').upper()} | "
            f"Confianza {regime.get('confidence', 0):.0%} | "
            f"{regime.get('description', '')}"
        )
    except:
        pass

    try:
        top = fetch_top_cryptos(limit=50)
        sorted_by_change = sorted(
            top,
            key=lambda x: x["quote"]["USD"].get("percent_change_24h", 0) or 0,
            reverse=True
        )
        gainers = sorted_by_change[:3]
        losers  = sorted_by_change[-3:]

        g_str = ", ".join(
            f"{c['symbol']} +{c['quote']['USD']['percent_change_24h']:.1f}%"
            for c in gainers
        )
        l_str = ", ".join(
            f"{c['symbol']} {c['quote']['USD']['percent_change_24h']:.1f}%"
            for c in losers
        )
        parts.append(f"TOP GAINERS HOY: {g_str}")
        parts.append(f"TOP LOSERS HOY: {l_str}")
    except:
        pass

    try:
        db = SessionLocal()
        from datetime import timedelta
        since   = datetime.utcnow() - timedelta(hours=8)
        alerts  = db.query(Alert).filter(
            Alert.triggered_at >= since,
            Alert.is_active == 1,
            Alert.severity.in_(["high", "critical"])
        ).order_by(Alert.triggered_at.desc()).limit(5).all()
        db.close()

        if alerts:
            alert_str = " | ".join(f"{a.symbol}: {a.title}" for a in alerts)
            parts.append(f"ALERTAS ACTIVAS: {alert_str}")
    except:
        pass

    return "\n".join(parts)

def generate_briefing(context_type: str) -> dict:
    """
    Genera un briefing de mercado según el contexto solicitado.
    context_type: morning | evening | weekly | alert
    """
    cache_key = f"briefing_{context_type}"
    ttl_map   = {
        "morning": 3600,
        "evening": 3600,
        "weekly":  86400,
        "alert":   900
    }
    ttl = ttl_map.get(context_type, 1800)

    cached = get_cached(cache_key, ttl_seconds=ttl)
    if cached:
        cached["from_cache"] = True
        return cached

    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY no configurada"}

    context = build_briefing_context(context_type)

    tone_map = {
        "morning": "Es el briefing matutino. El usuario quiere saber qué pasó mientras dormía y cómo arrancar el día.",
        "evening": "Es el briefing vespertino. Resume lo más importante del día y qué vigilar esta noche.",
        "weekly":  "Es el resumen semanal. Analiza la semana completa, tendencias y outlook para la próxima.",
        "alert":   "Hay condiciones urgentes en el mercado. Sé directo y conciso sobre qué está pasando ahora mismo."
    }
    tone = tone_map.get(context_type, "Genera un resumen general del mercado.")

    prompt = f"""Eres un analista financiero cripto senior generando un briefing ejecutivo.
{tone}

DATOS DEL MERCADO:
{context}

Genera un briefing ejecutivo. Responde ÚNICAMENTE con JSON válido, sin texto adicional:
{{
  "headline": "Título de máximo 10 palabras que capture lo más importante",
  "summary": "Párrafo de 3-4 oraciones con el estado actual del mercado",
  "key_events": ["evento importante 1", "evento importante 2", "evento importante 3"],
  "watch_list": ["activo o nivel a vigilar 1", "activo o nivel a vigilar 2"],
  "sentiment": "bullish | bearish | neutral | mixed",
  "confidence": 0.0
}}"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":  "application/json"
            },
            json={
                "model":       GROQ_MODEL,
                "messages":    [{"role": "user", "content": prompt}],
                "max_tokens":  600,
                "temperature": 0.3
            },
            timeout=30
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()

        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        result = json.loads(content)
        result["context"]      = context_type
        result["generated_at"] = datetime.utcnow().isoformat()
        result["from_cache"]   = False

        set_cache(cache_key, result)
        return result

    except Exception as e:
        return {"error": str(e), "context": context_type}