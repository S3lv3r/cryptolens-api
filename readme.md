# CryptoLens Intelligence API — Documentación de Endpoints

**Base URL:** https://cryptolens-api-production.up.railway.app
**Documentación interactiva:** https://cryptolens-api-production.up.railway.app/docs  
**Versión:** 2.0.0  

---

## Arquitectura general

La API funciona con un sistema de dos capas:

### Capa de recolección
Un scheduler interno corre en segundo plano y actualiza los datos automáticamente sin que el cliente tenga que hacer nada.  
Los datos siempre están listos y precalculados.

### Capa de exposición
Los endpoints simplemente leen lo que ya está calculado en la base de datos y lo devuelven en milisegundos.  
Sin cálculos en tiempo real, sin esperas.

---

## Intervalos de actualización automática

| Proceso                | Frecuencia  | Qué hace |
|----------------------|------------|----------|
| Datos de mercado     | Cada 5 min | Precios, volumen, market cap del top 50 |
| Indicadores y señales| Cada 30 min| EMA, MACD, RSI, ADX, Bollinger, señales |
| Actividad de ballenas| Cada hora  | Detecta spikes de volumen inusuales |
| Trending             | Cada 30 min| Gainers, losers, más visitadas |

---

# Endpoints

## General

### GET /
Verificación de que la API está activa.

    {
      "message": "CryptoLens Intelligence API",
      "version": "2.0.0"
    }

---

### GET /admin/refresh
Fuerza la actualización manual de todos los datos sin esperar el scheduler.  
Útil durante desarrollo o cuando se necesitan datos frescos inmediatamente.

    {
      "message": "Datos actualizados"
    }

---

## Market — Datos de Mercado

### GET /market/top50
Devuelve los datos de mercado más recientes del Top 50 criptomonedas ordenadas por capitalización de mercado.  
Solo devuelve el registro más reciente por activo, sin duplicados.

    [
      {
        "symbol": "BTC",
        "name": "Bitcoin",
        "price_usd": 84500.0,
        "market_cap": 1672000000000.0,
        "volume_24h": 38000000000.0,
        "change_24h": 2.35,
        "change_7d": 5.12,
        "timestamp": "2026-04-20T10:00:00"
      }
    ]

### GET /market/history/{symbol}?hours={horas}
Devuleve el historial de precios desde la DB local.
Es util para graficas de linea de precios con volumen.
En la variable {horas} son horas hacia atras, por default esta 24 y maximo es 168 (7 dias)

    [
        {
            {
              "symbol": "BTC",
              "name": "Bitcoin",
              "hours": 32,
              "count": 383,
              "data": [
                {
                  "timestamp": "2026-04-25T19:51:21",
                  "price_usd": 77230.8,
                  "volume_24h": 18854600000,
                  "market_cap": 1546210000000,
                  "change_24h": -0.47215
                },
                {
                  "timestamp": "2026-04-25T19:56:21",
                  "price_usd": 77272.1,
                  "volume_24h": 18845600000,
                  "market_cap": 1547040000000,
                  "change_24h": -0.433281
                },
                {
                  "timestamp": "2026-04-25T20:01:21",
                  "price_usd": 77323.8,
                  "volume_24h": 18747200000,
                  "market_cap": 1548080000000,
                  "change_24h": -0.413487
                },
                {
                  "timestamp": "2026-04-25T20:06:21",
                  "price_usd": 77342.1,
                  "volume_24h": 18654600000,
                  "market_cap": 1548440000000,
                  "change_24h": -0.297903
                }
            }
        }
    ]

---

## Analysis — Indicadores Técnicos

### GET /analysis/{symbol}

Devuelve el análisis técnico completo del activo especificado. Los indicadores están organizados por categoría para facilitar su interpretación.

Parámetros:
- symbol — BTC, ETH, SOL
    
        {
          "symbol": "BTC",
          "name": "Bitcoin",
          "timestamp": "2026-04-20T10:00:00",
          "trend": {
            "ema_9": 83200.0,
            "ema_21": 81500.0,
            "ema_50": 78000.0,
            "lsma_25": 82100.0,
            "lsma_200": 65000.0
          },
          "momentum": {
            "rsi": 58.4,
            "macd": 320.5,
            "macd_signal": 290.1,
            "macd_histogram": 30.4
          },
          "volatility": {
            "bb_upper": 88000.0,
            "bb_middle": 83000.0,
            "bb_lower": 78000.0,
            "bb_pct_b": 0.65
          },
          "strength": {
            "adx": 34.2,
            "trend_strength": "tendencia moderada"
          }
        }


### Guía de interpretación

| Indicador | Qué mide | Señal alcista | Señal bajista |
|----------|--------|--------------|--------------|
| RSI | Momentum | < 30 (sobreventa) | > 70 (sobrecompra) |
| MACD | Tendencia | MACD > señal | MACD < señal |
| BB %B | Posición | < 0.1 | > 0.9 |
| ADX | Fuerza | > 40 | < 20 |
| EMA 9 vs 21 | Cruce | EMA9 > EMA21 | EMA9 < EMA21 |
| LSMA 200 | Macro | Precio > LSMA200 | Precio < LSMA200 |

### GET /history/{symbol}

Historial de indicadores tecnicos calculados.
Es util para graficar RSI, MACD y Bollinger en el tiempo.
Tiene 50 registros historicos

    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "count": 50,
      "data": [
            {
              "timestamp": "2026-04-26T03:06:22",
              "rsi": 62.71,
              "macd": 2075.32,
              "macd_signal": 1809.17,
              "macd_histogram": 266.147,
              "bb_upper": 79845.1,
              "bb_middle": 74472.3,
              "bb_lower": 69099.5,
              "bb_pct_b": 0.7941,
              "ema_9": 76624.9,
              "ema_21": 74600,
              "adx": 35.47
            },
            {
              "timestamp": "2026-04-26T03:36:22",
              "rsi": 62.71,
              "macd": 2075.32,
              "macd_signal": 1809.17,
              "macd_histogram": 266.147,
              "bb_upper": 79845.1,
              "bb_middle": 74472.3,
              "bb_lower": 69099.5,
              "bb_pct_b": 0.7941,
              "ema_9": 76624.9,
              "ema_21": 74600,
              "adx": 35.47
            },
            {
              "timestamp": "2026-04-26T04:06:22",
              "rsi": 62.71,
              "macd": 2075.32,
              "macd_signal": 1809.17,
              "macd_histogram": 266.147,
              "bb_upper": 79845.1,
              "bb_middle": 74472.3,
              "bb_lower": 69099.5,
              "bb_pct_b": 0.7941,
              "ema_9": 76624.9,
              "ema_21": 74600,
              "adx": 35.47
            }
        ]
    }

---

## Ohlcv - Velas Japones e histograma de volumen

### GET /ohlcv/{symbol}?days={dias}

Con este endpoint se logra realizar velas japonesas e histogramas de volumen.
Devuelve datos OHLCV diarios.
En la variable dias, son numero de dias hacia atras (1-60)

    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "days": 5,
      "count": 4,
      "data": [
        {
          "timestamp": "2026-04-23T00:00:00.000Z",
          "open": 78203.873186,
          "high": 78676.939081,
          "low": 77014.452508,
          "close": 78268.954108,
          "volume": 40354900915.57,
          "market_cap": 1566830481949.34
        },
        {
          "timestamp": "2026-04-24T00:00:00.000Z",
          "open": 78263.823773,
          "high": 78554.094933,
          "low": 77318.446412,
          "close": 77455.315618,
          "volume": 32784213526.2,
          "market_cap": 1550717824694.32
        },
        {
          "timestamp": "2026-04-25T00:00:00.000Z",
          "open": 77457.21407,
          "high": 77882.642288,
          "low": 77184.661975,
          "close": 77612.017875,
          "volume": 16702933134.07,
          "market_cap": 1553873094608.76
        },
        {
          "timestamp": "2026-04-26T00:00:00.000Z",
          "open": 77613.119477,
          "high": 78923.562966,
          "low": 77334.888559,
          "close": 78657.539423,
          "volume": 21482934749.76,
          "market_cap": 1574890108360.41
        }
      ]
    }

---

## Signal — Motor de Decisión

### GET /signal/{symbol}

El endpoint más importante de la API. Integra todos los indicadores técnicos y la actividad de mercado para generar una recomendación clara de inversión con análisis por horizonte temporal.

    {
      "symbol": "ETH",
      "name": "Ethereum",
      "timestamp": "2026-04-20T10:00:00",
      "market": {
        "price_usd": 2345.0,
        "change_24h": -1.2,
        "volume_24h": 14000000000.0
      },
      "recommendation": {
        "action": "BUY",
        "confidence": 0.74,
        "explanation": "RSI en sobreventa, posible rebote | MACD con momentum alcista | EMA 9 sobre EMA 21, tendencia alcista de corto plazo | Precio sobre LSMA 200, tendencia macro alcista",
        "whale_alert": "Spike de volumen +230% con precio subiendo +6.1%. Posible acumulación institucional."
      },
      "horizons": {
        "short_term": {
          "label": "Corto plazo (1-7 días)",
          "action": "BUY",
          "risk": "bajo",
          "notes": "RSI en sobreventa, posible rebote | Momentum a favor en corto plazo"
        },
        "medium_term": {
          "label": "Mediano plazo (1-3 meses)",
          "action": "BUY",
          "notes": "Tendencia de mediano plazo positiva, posible continuación alcista"
        },
        "long_term": {
          "label": "Largo plazo (+6 meses)",
          "action": "BUY",
          "notes": "Estructura de largo plazo alcista | Tendencia fuerte y sostenida"
        }
      },
      "indicators": {
        "rsi": 28.4,
        "macd": 45.2,
        "adx": 38.1,
        "bb_pct_b": 0.08,
        "ema_9": 2310.0,
        "ema_21": 2290.0,
        "lsma_25": 2280.0
      }
  }

Valores posibles:
- action: BUY | SELL | HOLD  
- risk: bajo | medio | alto  

Interpretación de confidence:

| Rango | Interpretación |
|------|--------------|
| 0.0 – 0.5 | Señal débil |
| 0.5 – 0.7 | Moderada |
| 0.7 – 0.85 | Fuerte |
| 0.85 – 0.95 | Muy fuerte |

---

## Ranking

### GET /ranking

Devuelve todos los activos del top 50 ordenados por capitalización de mercado, incluyendo la señal actual de cada uno. Permite identificar dónde está el dinero y qué activos están sobreperformando sin analizar uno por uno.

    [
      {
        "rank": 1,
        "symbol": "BTC",
        "name": "Bitcoin",
        "price_usd": 84500.0,
        "market_cap": 1672000000000.0,
        "change_24h": 2.35,
        "signal": "HOLD"
      }
    ]

---

## Whales

### GET /whales

Devuelve eventos de actividad inusual de grandes actores del mercado, detectados mediante análisis de spikes de volumen. Un spike de volumen superior al 150% respecto al promedio es una señal estadísticamente significativa de movimiento institucional o de ballenas.

Parámetros opcionales:
- symbol — Filtra por activo. Ejemplo: ?symbol=BTC
- limit — Número de resultados. Default: 50. Ejemplo: ?limit=10
- source — db (default, rápido) o live (consulta CMC en tiempo real)

Ejemplo: GET /whales?symbol=ETH&limit=5

    
      {
        "symbol": "ETH",
        "amount_usd": 2400000000.0,
        "transaction_type": "accumulation",
        "interpretation": "...",
        "timestamp": "2026-04-20T08:00:00"
      }
    
### Tipos de transacción:

| Tipo | Significado |
|------|--------------|
| accumulation | Volumen alto + precio sube → posible compra institucional |
| exchange_deposit | Volumen alto + precio baja → posible venta masiva |
| unusual_activity | Volumen alto sin dirección clara → monitorear |

---

## Altcoin Season

### GET /altcoin-season

Detecta automáticamente en qué fase del ciclo de mercado se encuentra el usuario. Fundamental para contextualizar cualquier decisión de inversión.

    {
      "season": "Altcoin Season",
      "score": 78
    }

---

## Trending

### GET /trending

Devuelve las criptomonedas con mayor tracción en el mercado ahora mismo. Se actualiza cada 30 minutos. Útil para detectar movimientos de dinero inteligente y oportunidades emergentes antes de que se reflejen en el precio.

    {
      "trending": [],
      "gainers": [],
      "losers": [],
      "most_visited": []
    }

---

## Categories

### GET /categories

Devuelve el rendimiento agregado por sector del mercado cripto. Permite identificar qué narrativa o sector está liderando el ciclo actual sin analizar activo por activo.

    [
      {
        "name": "DeFi",
        "avg_price_change": 8.4,
        "market_cap": 95000000000.0,
        "volume": 12000000000.0,
        "num_tokens": 287
      }
    ]

---

## News

### GET /news

Devuelve las últimas noticias del mercado cripto desde CoinDesk. Se cachea 15 minutos para no saturar la fuente. Proporciona contexto fundamental que complementa el análisis técnico.

    [
      {
        "title": "Bitcoin surpasses $85K as institutional demand grows",
        "link": "https://coindesk.com/...",
        "description": "Bitcoin reached a new monthly high...",
        "published": "Mon, 20 Apr 2026 09:30:00 GMT",
        "source": "CoinDesk"
      }
    ]

---

## Performance

### GET /performance/{symbol}

Devuelve el rendimiento del precio de un activo en múltiples horizontes temporales. Complementa la señal con contexto histórico real para que el usuario pueda evaluar si un activo ha tenido momentum sostenido.

    {
      "BTC": {
        "periods": {
          "yesterday": {
            "open": 82000.0,
            "close": 84500.0,
            "percent_change": 3.05
          },
          "last_week": {
            "open": 79000.0,
            "close": 84500.0,
            "percent_change": 6.96
          },
          "last_month": {
            "open": 71000.0,
            "close": 84500.0,
            "percent_change": 19.01
          }
        }
      }
    }

---

-- Version 3.0.0  --

## IA 

### POST /ai/analyze

Envia una pregunta en lenguaje natural y la IA responde usando todos los datos
tecnicos disponibles del activo

BODY

      {
        "symbol": {symbol},
        "query": {prompt}
      }

EJEMPLOS DE QUERIES

    { "symbol": "BTC", 
    "query": "¿Cómo está el mercado de Bitcoin hoy?" 
    }

    { "symbol": "ETH", 
    "query": "¿Está ETH en zona de sobrecompra?" 
    }

    { "symbol": "SOL", 
    "query": "Analiza la tendencia de SOL en múltiples timeframes" 
    }

    { "symbol": "XRP", 
    "query": "¿Qué dice la estructura de mercado de XRP?" 
    }

    { "symbol": "BTC", 
    "query": "¿Es buen momento para entrar al mercado según los indicadores?" 
    }

RESPUESTA

    {
      "symbol": "XLM",
      "query": "Analiza XLM estos últimos días",
      "analysis": "Stellar (XLM) muestra una estructura de mercado en consolidación...",
      "tokens_used": 847,
      "model": "llama-3.3-70b-versatile",
      "context_used": "PRECIO ACTUAL: $0.172928 USD | Cambio 24h: -1.2% ..."
    }

### POST /ai/compare

Compara 2-4 activos usando IA con datos reales de cada uno.

BODY

    {
        "symbols": {[symbol,symbol,symbol,symbol]},
        "query": {prompt}
    }

EJEMLPLOS DE QUERIES

    {
        "symbols": ["BTC", "ETH"],
        "query": "¿Cuál está más fuerte técnicamente esta semana?"
    }
    {
        "symbols": ["DOGE", "SHIB", "PEPE"],
        "query": "¿Cuál de los memecoins tiene mejor setup técnico?"
    }
    {
        "symbols": ["BTC", "ETH", "SOL", "BNB"],
        "query": "Rankéalos de mejor a peor setup técnico actual"
    }

RESPUESTA

    {
        "symbols": ["ETH", "SOL"],
        "query": "¿Cuál tiene mejor setup técnico ahora mismo?",
        "comparison": "Comparando ETH y SOL con sus datos actuales...\n\nEthereum muestra RSI de 52.3 en zona neutral con MACD positivo...\nSolana presenta RSI de 61.2 con tendencia alcista más pronunciada...",
        "tokens_used": 1102,
        "model": "llama-3.3-70b-versatile"
    }

---

## Narrative 

### GET /narrative/{symbol}

Narrativa de mercado generada con IA.
Incluye summary, bull_case, bear_case, risk_factors y market_context.
Se cachea 30 minutos.

    {
        "symbol": "BTC",
        "name": "Bitcoin",
        "summary": "Bitcoin consolida por encima del soporte clave de $83,000 con momentum alcista en timeframes altos y RSI en zona neutral.",
        "bull_case": "Si mantiene $83,000 como soporte y rompe $86,500 con volumen, el siguiente objetivo es $90,000-$92,000.",
        "bear_case": "Una ruptura de $81,000 con volumen significativo abriría camino hacia $76,000 y posiblemente $72,000.",
        "risk_factors": [
            "RSI en 4h acercándose a zona de sobrecompra (67)",
            "Funding rate elevado indica exceso de longs",
            "Volumen decreciente en el rally — falta convicción"
        ],
        "market_context": "Mercado en régimen de acumulación con dominancia BTC en 42%. Capital rotando hacia altcoins de mediana capitalización.",
        "key_level": "$83,000 — soporte crítico a vigilar",
        "generated_at": "2026-04-20T10:00:00"
    }

---

## Briefing

### GET /briefing/{context}

Briefing de mercado generado con IA según el contexto.
<br><br>
Contextos disponibles:<br>
    - morning → qué pasó mientras dormías, cómo arrancar el día<br>
    - evening → resumen del día, qué vigilar esta noche<br>
    - weekly  → resumen semanal y outlook próxima semana<br>
    - alert   → condiciones urgentes ahora mismo<br>

Se cachea automáticamente según el contexto.

| Contexto | Cuándo usarlo | 
|------|------------|
| morning | Al abrir la app por la mañana |
| evening | Resumen al final del día |
| weekly | Resumen los lunes o domingos |
| alert | Cuando hay movimientos bruscos |

    {
        "headline": "Bitcoin consolida mientras altcoins lideran el mercado",
        "summary": "El mercado cripto amanece en modo acumulación con el top 50 mostrando 72% de activos en verde. Bitcoin mantiene $84,000 como soporte mientras Solana y Ethereum lideran las ganancias del día con +5.2% y +3.8% respectivamente.",
        "key_events": [
            "SOL rompe resistencia clave de $145 con volumen 180% sobre promedio",
            "BTC dominancia cae a 42.1% — señal de rotación hacia altcoins",
            "Funding rates normalizados tras liquidaciones de la semana pasada"
        ],
        "watch_list": [
            "BTC $83,000 — soporte crítico a vigilar",
            "ETH $2,400 — resistencia a superar para continuar rally"
        ],
        "sentiment": "bullish",
        "confidence": 0.72,
        "context": "morning",
        "generated_at": "2026-04-20T07:00:00",
        "from_cache": false
    }

---

## Multi-Timeframe

### GET /analysis/{symbol}/multi-timeframe

Análisis técnico completo en 5 timeframes independientes.
Incluye consenso global y alignment score entre temporalidades.

    {
      "symbol": "BTC",
      "timestamp": "2026-04-20T10:00:00",
      "consensus": {
        "bias": "bullish",
        "alignment_score": 0.85,
        "confidence": 0.80,
        "bullish_timeframes": ["1h", "4h", "1d", "1w"],
        "bearish_timeframes": ["15m"],
        "neutral_timeframes": [],
        "timeframes_analyzed": 5
      },
      "timeframes": {
        "15m": { "rsi": 68.2, "trend_direction": "bearish", ... },
        "1h":  { "rsi": 55.1, "trend_direction": "bullish", ... },
        "4h":  { "rsi": 61.3, "trend_direction": "bullish", ... },
        "1d":  { "rsi": 58.4, "trend_direction": "strong_bullish", ... },
        "1w":  { "rsi": 62.1, "trend_direction": "bullish", ... }
      }
    }

---

## Structure

### GET /structure/{symbol}?timeframe={timeframe}

Análisis de estructura de mercado.
Detecta HH/HL/LH/LL, BOS, CHOCH, soportes, resistencias y zonas de liquidez.

{timeframe} = 15m, 1h, 4h, 1d, 1w (por dafault esta en: 1d)

    {
      "symbol": "BTC",
      "timeframe": "1d",
      "current_price": 84500.0,
      "market_structure": "uptrend",
      "trend_phase": "continuation",
      "swing_high": 86000.0,
      "swing_low": 79000.0,
      "current_resistance": 86000.0,
      "current_support": 81000.0,
      "liquidity_zone_high": 87500.0,
      "liquidity_zone_low": 78000.0,
      "last_bos": {
        "detected": true,
        "price": 82000.0,
        "direction": "bullish"
      },
      "last_choch": {
        "detected": false,
        "price": null,
        "direction": null
      }
    }

---

## Volatility

### GET /volatility/{symbol}?timeframe={timeframe}

Análisis de volatilidad contextual.
Incluye ATR, volatilidad histórica, percentil y régimen de volatilidad.

{timeframe} = 15m, 1h, 4h, 1d, 1w (deafult: 1d)

    {
      "symbol": "BTC",
      "timeframe": "1d",
      "current_price": 84500.0,
      "atr": 2340.5,
      "atr_pct": 2.77,
      "historical_volatility": 48.3,
      "volatility_percentile": 62.4,
      "regime": "normal",
      "market_condition": "Volatilidad normal. Condiciones estándar de mercado."
    }

---

## Market Regime

### Get /market-regime

Clasificación del estado global del mercado.<br>
Estados: trending, ranging, euphoric, panic, accumulation, distribution<br>
Se cachea 15 minutos.

| Regimen | Descripción |
|------|------------|
| trending | Mercado en tendencia con expansión de volumen |
| ranging | Mercado lateral sin dirección clara |
| euphoric | RSI extremo, volumen expansivo — alto riesgo |
| panic | Ventas masivas generalizadas |
| accumulation | Capital entrando, preferencia por altcoins |
| distribution | Capital rotando hacia BTC o saliendo |

    {
      "regime": "accumulation",
      "confidence": 0.75,
      "description": "Acumulación detectada. Capital entrando al mercado con preferencia por altcoins.",
      "metrics": {
        "btc_dominance": 42.3,
        "btc_rsi": 55.2,
        "aggregate_rsi": 58.1,
        "breadth": 0.72,
        "advancing": 36,
        "declining": 14,
        "vol_change_24h": 12.4,
        "mcap_change_24h": 2.1,
        "total_market_cap": 2800000000000,
        "total_volume_24h": 180000000000
      }
    }

---

## Derivatives

### GET /derivatives/{symbol}

Datos de mercado de derivados desde Binance Futures.
Incluye funding rate, open interest, ratio long/short y order book.

    {
      "symbol": "BTC",
      "funding_rate": {
        "symbol": "BTC",
        "funding_rate": 0.0001,
        "funding_time": 1713600000000
      },
      "open_interest": {
        "symbol": "BTC",
        "open_interest": 85432.12,
        "timestamp": 1713600000000
      },
      "long_short_ratio": {
        "symbol": "BTC",
        "long_ratio": 0.58,
        "short_ratio": 0.42,
        "timestamp": 1713600000000
      },
      "order_book": {
        "symbol": "BTC",
        "best_bid": 84490.0,
        "best_ask": 84510.0,
        "bid_volume": 12.43,
        "ask_volume": 9.87,
        "pressure": "buy",
        "top_bids": [[84490, 2.1], [84480, 3.2], ...],
        "top_asks": [[84510, 1.8], [84520, 2.4], ...]
      }
    }

Interpretacion del funding rate

| Valor | Significado |
|------|------------|
| > 0.01% | Mercado alcista, longs pagando a shorts |
| < -0.01% | Mercado bajista, shorts pagando a longs |
| ≈ 0 | Mercado equilibrado |

---

## Alerts

### GET /alerts/triggered

Devuelve todas las alertas activas detectadas automáticamente.
No requiere configuración — la API detecta condiciones notables sola.
hours: últimas N horas (1-168)
severity: low | medium | high | critical
symbol: filtrar por activo

Filtro de Horas:

    GET /alerts/triggered?hours=6
    GET /alerts/triggered?hours=48
    GET /alerts/triggered?hours=168

Filtro de severidad

    GET /alerts/triggered?severity=critical
    GET /alerts/triggered?severity=high
    GET /alerts/triggered?severity=medium
    GET /alerts/triggered?severity=low

Filtro de simbolo

    GET /alerts/triggered?symbol=BTC
    GET /alerts/triggered?symbol=ETH
    GET /alerts/triggered?symbol=SOL

Combinados

    GET /alerts/triggered?hours=12&severity=high
    GET /alerts/triggered?hours=24&severity=critical&symbol=BTC
    GET /alerts/triggered?hours=6&symbol=ETH

Respuesta

    {
        "total": 3,
        "hours": 24,
        "severity": null,
        "alerts": [
            {
                "id": 47,
                "symbol": "XRP",
                "alert_type": "volume_spike",
                "severity": "critical",
                "title": "XRP spike de volumen +340%",
                "message": "Volumen inusual detectado en XRP: +340% sobre el promedio. Posible movimiento institucional.",
                "data": {
                    "volume_change_pct": 340.2,
                    "current_volume": 8500000000
                },
                "triggered_at": "2026-04-20T14:28:00"
            },
            {
                "id": 46,
                "symbol": "BTC",
                "alert_type": "rsi_overbought",
                "severity": "high",
                "title": "BTC RSI en sobrecompra (78.3)",
                "message": "RSI de BTC alcanzó 78.3, zona de sobrecompra. Posible corrección próxima.",
                "data": { "rsi": 78.3 },
                "triggered_at": "2026-04-20T12:00:00"
            },
            {
                "id": 45,
                "symbol": "ETH",
                "alert_type": "signal_change",
                "severity": "high",
                "title": "ETH cambió señal: HOLD → BUY",
                "message": "La señal de ETH cambió de HOLD a BUY con confianza del 74%.",
                "data": {
                    "previous": "HOLD",
                    "current": "BUY",
                    "confidence": 0.74
                },
                "triggered_at": "2026-04-20T10:30:00"
            }
        ]
    }

### GET /alerts/scan/{symbol}

Escanea un activo específico ahora mismo y devuelve alertas detectadas.
Guarda las nuevas en DB automáticamente.

    {
        "symbol": "XRP",
        "scanned_at": "2026-04-20T14:30:00",
        "alerts_found": 2,
        "alerts": [
            {
                "symbol": "XRP",
                "alert_type": "volume_spike",
                "severity": "critical",
                "title": "XRP spike de volumen +340%",
                "message": "Volumen inusual detectado en XRP...",
                "data": { "volume_change_pct": 340.2 }
            },
            {
                "symbol": "XRP",
                "alert_type": "rsi_overbought",
                "severity": "medium",
                "title": "XRP RSI en sobrecompra (71.2)",
                "message": "RSI de XRP alcanzó 71.2...",
                "data": { "rsi": 71.2 }
            }
        ]
    }

---



## Códigos de respuesta

| Código | Significado |
|------|------------|
| 200 | Éxito |
| 404 | Activo no encontrado |
| 500 | Error interno |

---

## Flujo recomendado

Al abrir la plataforma:
1. GET /briefing/morning          
2. GET /alerts/triggered?hours=8  
3. GET /altcoin-season  
4. GET /market/top50 

En La plataforma

5. GET /ranking  
6. GET /trending  
7. GET /signal/{symbol}  
8. GET /analysis/{symbol}  
9. GET /whales  
10. GET /news  

Para análisis avanzado

11. POST /ai/analyze               
12. POST /ai/compare 

Cuando hay movimiento brusco

13. GET /briefing/alert           
14. GET /alerts/triggered?severity=critical 

---

##  Notas importantes

- Rate limiting — CoinMarketCap: 30 requests/minuto  
- Datos en tiempo real vs precalculados  
- Símbolos case-insensitive  
- Base de datos guarda snapshots cada 5 minutos  