import requests
from config import GROQ_API_KEY, GROQ_MODEL
from database import SessionLocal
from models import Crypto, Signal, MarketData, TechnicalIndicator

def build_narrative_context(symbol: str) -> dict:
    db = SessionLocal()
    try:
        crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
        if not crypto:
            return {}

        market = (
            db.query(MarketData)
            .filter(MarketData.crypto_id == crypto.id)
            .order_by(MarketData.timestamp.desc())
            .first()
        )
        signal = (
            db.query(Signal)
            .filter(Signal.crypto_id == crypto.id)
            .order_by(Signal.timestamp.desc())
            .first()
        )
        ind = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.crypto_id == crypto.id)
            .order_by(TechnicalIndicator.timestamp.desc())
            .first()
        )

        return {
            "symbol":     crypto.symbol,
            "name":       crypto.name,
            "price":      market.price_usd   if market else None,
            "change_24h": market.change_24h  if market else None,
            "change_7d":  market.change_7d   if market else None,
            "volume":     market.volume_24h  if market else None,
            "signal":     signal.action      if signal else None,
            "confidence": signal.confidence  if signal else None,
            "explanation":signal.explanation if signal else None,
            "rsi":        ind.rsi            if ind else None,
            "macd":       ind.macd           if ind else None,
            "adx":        ind.adx            if ind else None,
            "bb_pct_b":   ind.bb_pct_b       if ind else None,
            "ema_9":      ind.ema_9           if ind else None,
            "ema_21":     ind.ema_21          if ind else None,
        }
    finally:
        db.close()

def generate_narrative(symbol: str) -> dict:
    """
    Genera narrativa de mercado estructurada usando IA.
    Devuelve summary, bull_case, bear_case, risk_factors y market_context.
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY no configurada"}

    ctx = build_narrative_context(symbol)
    if not ctx:
        return {"error": f"{symbol} no encontrado"}

    prompt = f"""Eres un analista de criptomonedas senior. Analiza estos datos de {ctx['name']} ({ctx['symbol']}) y genera una narrativa estructurada.

DATOS ACTUALES:
- Precio: ${ctx['price']:,.6f} USD
- Cambio 24h: {ctx['change_24h']:.2f}%
- Cambio 7d: {ctx['change_7d']:.2f}%
- Volumen 24h: ${ctx['volume']:,.0f}
- Señal: {ctx['signal']} (confianza {ctx['confidence']:.0%})
- RSI: {ctx['rsi']}
- MACD: {ctx['macd']:.4f}
- ADX: {ctx['adx']}
- BB%B: {ctx['bb_pct_b']}
- EMA9: {ctx['ema_9']:.4f} | EMA21: {ctx['ema_21']:.4f}
- Razones de señal: {ctx['explanation']}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta, sin texto adicional:
{{
  "summary": "1-2 oraciones describiendo el estado actual del mercado de {ctx['symbol']}",
  "bull_case": "Escenario alcista específico con niveles de precio si es posible",
  "bear_case": "Escenario bajista específico con niveles de precio si es posible",
  "risk_factors": ["factor 1", "factor 2", "factor 3"],
  "market_context": "Contexto macro y posicionamiento del activo en el mercado actual",
  "key_level": "Nivel de precio más importante a vigilar ahora mismo"
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
                "max_tokens":  800,
                "temperature": 0.2
            },
            timeout=30
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"].strip()

        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        import json
        narrative = json.loads(content)
        narrative["symbol"]       = ctx["symbol"]
        narrative["name"]         = ctx["name"]
        narrative["generated_at"] = __import__("datetime").datetime.utcnow().isoformat()
        return narrative

    except Exception as e:
        return {"error": str(e), "symbol": symbol}