import requests
from config import GROQ_API_KEY, GROQ_MODEL
from services.market_service import fetch_top_cryptos
from services.binance_service import fetch_klines
from services.multi_timeframe_service import analyze_timeframe, calculate_consensus
from services.volatility_service import analyze_volatility
from services.market_structure_service import detect_market_structure
from database import SessionLocal
from models import Crypto, Signal, MarketData, TechnicalIndicator

def build_market_context(symbol: str) -> str:
    """
    Recopila todos los datos disponibles del activo
    y los convierte en contexto para la IA.
    """
    db = SessionLocal()
    context_parts = []

    try:
        crypto = db.query(Crypto).filter(Crypto.symbol == symbol.upper()).first()
        if not crypto:
            return f"No se encontró información sobre {symbol} en la base de datos."

        market = (
            db.query(MarketData)
            .filter(MarketData.crypto_id == crypto.id)
            .order_by(MarketData.timestamp.desc())
            .first()
        )
        if market:
            context_parts.append(
                f"PRECIO ACTUAL: ${market.price_usd:,.6f} USD | "
                f"Cambio 24h: {market.change_24h:.2f}% | "
                f"Cambio 7d: {market.change_7d:.2f}% | "
                f"Volumen 24h: ${market.volume_24h:,.0f} | "
                f"Market Cap: ${market.market_cap:,.0f}"
            )

        signal = (
            db.query(Signal)
            .filter(Signal.crypto_id == crypto.id)
            .order_by(Signal.timestamp.desc())
            .first()
        )
        if signal:
            context_parts.append(
                f"SEÑAL ACTUAL: {signal.action} | "
                f"Confianza: {signal.confidence:.0%} | "
                f"Razones: {signal.explanation}"
            )
            if signal.short_term_notes:
                context_parts.append(f"CORTO PLAZO (1-7d): {signal.short_term_action} — {signal.short_term_notes}")
            if signal.medium_term_notes:
                context_parts.append(f"MEDIANO PLAZO (1-3m): {signal.medium_term_action} — {signal.medium_term_notes}")
            if signal.long_term_notes:
                context_parts.append(f"LARGO PLAZO (+6m): {signal.long_term_action} — {signal.long_term_notes}")

        ind = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.crypto_id == crypto.id)
            .order_by(TechnicalIndicator.timestamp.desc())
            .first()
        )
        if ind:
            context_parts.append(
                f"INDICADORES TÉCNICOS: RSI={ind.rsi} | MACD={ind.macd:.4f} | "
                f"ADX={ind.adx} | BB%B={ind.bb_pct_b} | "
                f"EMA9={ind.ema_9:.4f} | EMA21={ind.ema_21:.4f} | "
                f"LSMA25={ind.lsma_25:.4f}"
            )

    finally:
        db.close()

    try:
        analyses  = {tf: analyze_timeframe(symbol.upper(), tf) for tf in ["1h", "4h", "1d"]}
        consensus = calculate_consensus(analyses)
        context_parts.append(
            f"CONSENSO MULTI-TIMEFRAME: {consensus['bias'].upper()} | "
            f"Alineación: {consensus['alignment_score']:.0%} | "
            f"Confianza: {consensus['confidence']:.0%}"
        )
        for tf, data in analyses.items():
            if data:
                context_parts.append(
                    f"  {tf}: {data['trend_direction']} | RSI={data['rsi']} | ADX={data['adx']}"
                )
    except Exception as e:
        context_parts.append(f"Multi-timeframe no disponible: {e}")

    try:
        vol = analyze_volatility(symbol.upper(), "1d")
        if "error" not in vol:
            context_parts.append(
                f"VOLATILIDAD: {vol['regime']} | "
                f"ATR={vol['atr']} ({vol['atr_pct']}%) | "
                f"Vol histórica={vol['historical_volatility']}% | "
                f"Percentil={vol['volatility_percentile']}%"
            )
    except:
        pass

    try:
        struct = detect_market_structure(symbol.upper(), "1d")
        if "error" not in struct:
            context_parts.append(
                f"ESTRUCTURA: {struct['market_structure']} | "
                f"Fase: {struct['trend_phase']} | "
                f"Soporte: {struct['current_support']} | "
                f"Resistencia: {struct['current_resistance']} | "
                f"BOS: {struct['last_bos']['detected']} | "
                f"CHOCH: {struct['last_choch']['detected']}"
            )
    except:
        pass

    return "\n".join(context_parts)

def ask_ai(symbol: str, query: str) -> dict:
    """
    Envía el contexto del activo + la pregunta del usuario a Groq/Llama3.
    Devuelve análisis en lenguaje natural.
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY no configurada"}

    context = build_market_context(symbol)

    system_prompt = """Eres un analista financiero experto en criptomonedas. 
Tu función es interpretar datos técnicos de mercado y explicarlos en lenguaje claro y directo.
Reglas:
- Usa los datos proporcionados, no inventes información
- Sé específico con números y porcentajes
- Menciona contradicciones entre indicadores si las hay
- No uses frases genéricas como "podría subir o bajar"
- Indica claramente el nivel de certeza de tu análisis
- No uses lenguaje de asesoría financiera ni recomiendas comprar/vender
- Analiza condiciones de mercado, no tomes decisiones por el usuario
- Responde siempre en español"""

    user_prompt = f"""Datos actuales de {symbol.upper()}:

{context}

Pregunta del usuario: {query}"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":  "application/json"
            },
            json={
                "model":       GROQ_MODEL,
                "messages": [
                    {"role": "system",  "content": system_prompt},
                    {"role": "user",    "content": user_prompt}
                ],
                "max_tokens":  1024,
                "temperature": 0.3
            },
            timeout=30
        )
        response.raise_for_status()
        data    = response.json()
        content = data["choices"][0]["message"]["content"]
        tokens  = data["usage"]["total_tokens"]

        return {
            "symbol":        symbol.upper(),
            "query":         query,
            "analysis":      content,
            "tokens_used":   tokens,
            "model":         GROQ_MODEL,
            "context_used":  context
        }

    except Exception as e:
        return {"error": str(e)}