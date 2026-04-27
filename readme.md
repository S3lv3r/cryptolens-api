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

## Códigos de respuesta

| Código | Significado |
|------|------------|
| 200 | Éxito |
| 404 | Activo no encontrado |
| 500 | Error interno |

---

## Flujo recomendado

1. GET /altcoin-season  
2. GET /market/top50  
3. GET /ranking  
4. GET /trending  
5. GET /signal/{symbol}  
6. GET /analysis/{symbol}  
7. GET /whales  
8. GET /news  

---

##  Notas importantes

- Rate limiting — CoinMarketCap: 30 requests/minuto  
- Datos en tiempo real vs precalculados  
- Símbolos case-insensitive  
- Base de datos guarda snapshots cada 5 minutos  