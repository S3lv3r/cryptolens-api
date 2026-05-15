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

    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY no configurada"}

    context = build_market_context(symbol)

    system_prompt = """Eres un analista financiero experto y decisivo en criptomonedas. 
Tu función es interpretar datos técnicos y darle a usuarios principiantes una respuesta clara, directa y accionable.

Reglas ESTRICTAS de tu comportamiento:
1. POSTURA DECISIVA: Si el usuario te pregunta si debe comprar, vender o esperar, DEBES responder con un "SÍ" o un "NO" claro al principio de tu respuesta. Prohibido evadir la pregunta o decir "no puedo dar consejos".
2. CRITERIO PROPIO: Asume el rol de experto. Si los indicadores son mixtos, usa tu criterio para dar un veredicto final. No uses frases cobardes o genéricas como "el precio podría subir o bajar".
3. ARGUMENTACIÓN: Justifica tu Sí o No usando los datos y números exactos del contexto proporcionado (RSI, tendencias, EMAs).
4. DESCARGO DE RESPONSABILIDAD: Al final de tu respuesta, OBLIGATORIAMENTE debes incluir un párrafo de cierre similar a este:
   "Nota: Este veredicto se basa estrictamente en la lectura de los datos técnicos actuales y no es una ciencia exacta ni una garantía de futuro. El mercado es volátil, usa esta información como apoyo para tomar tu propia decisión."
5. Responde siempre en español."""

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

def compare_assets(symbols: list, query: str) -> dict:
    """
    Compara múltiples activos usando IA con datos reales de cada uno.
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY no configurada"}

    if len(symbols) < 2 or len(symbols) > 4:
        return {"error": "Envía entre 2 y 4 símbolos para comparar"}

    # Construir contexto de cada activo
    contexts = {}
    for symbol in symbols:
        contexts[symbol.upper()] = build_market_context(symbol.upper())

    combined = "\n\n".join(
        f"=== {sym} ===\n{ctx}"
        for sym, ctx in contexts.items()
    )

    system_prompt = """Eres un analista financiero experto y decisivo en criptomonedas.
Tu función es comparar activos usando datos técnicos reales y darle al usuario una conclusión clara de cuál es mejor opción.

Reglas ESTRICTAS de tu comportamiento:
1. VEREDICTO CLARO: Debes elegir un ganador absoluto basado en los datos. No evadas la respuesta. Si el usuario pregunta cuál comprar, dile exactamente cuál tiene el mejor setup técnico.
2. ARGUMENTACIÓN: Justifica por qué uno es mejor que el otro usando métricas específicas de ambos contextos. Menciona los riesgos del perdedor.
3. CERO AMBIGÜEDAD: Prohibido decir "ambos son buenos" o "depende de tu perfil". Toma una postura como analista experto.
4. DESCARGO DE RESPONSABILIDAD: Al final de tu respuesta, OBLIGATORIAMENTE debes incluir un cierre similar a este:
   "⚠️ Nota: Esta elección se basa estrictamente en el análisis técnico actual y no asegura rendimientos futuros. Usa esta perspectiva como una guía para tomar tu propia decisión financiera."
5. Responde siempre en español."""

    user_prompt = f"""Compara estos activos con sus datos actuales:

{combined}

Pregunta: {query}"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":  "application/json"
            },
            json={
                "model":       GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt}
                ],
                "max_tokens":  1200,
                "temperature": 0.3
            },
            timeout=45
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        tokens  = r.json()["usage"]["total_tokens"]

        return {
            "symbols":     [s.upper() for s in symbols],
            "query":       query,
            "comparison":  content,
            "tokens_used": tokens,
            "model":       GROQ_MODEL
        }

    except Exception as e:
        return {"error": str(e)}