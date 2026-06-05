from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    market, analysis, signals, ranking, whales,
    altcoin_season, trending, categories, news,
    performance, ohlcv, multi_timeframe, structure,
    volatility, market_regime, derivatives, ai
)
from tasks.scheduler import start_scheduler, task_market_data, task_indicators_and_signals, task_whale_activity
from routers import ohlcv
from routers import narrative, alerts, briefing

app = FastAPI(
    title="API de inteligencia CryptoLens",
    description="Plataforma SaaS de análisis financiero cripto - Top 50 por capitalización de mercado",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Market
app.include_router(market.router,          prefix="/market",          tags=["Mercado"])
app.include_router(ranking.router,         prefix="/ranking",         tags=["Mercado"])
app.include_router(ohlcv.router,           prefix="/ohlcv",           tags=["Mercado"])
app.include_router(performance.router,     prefix="/performance",     tags=["Mercado"])

# Analysis
app.include_router(analysis.router,        prefix="/analysis",        tags=["Análisis"])
app.include_router(multi_timeframe.router, prefix="/analysis",        tags=["Análisis"])
app.include_router(structure.router,       prefix="/structure",       tags=["Análisis"])
app.include_router(volatility.router,      prefix="/volatility",      tags=["Análisis"])

# Signals
app.include_router(signals.router,         prefix="/signal",          tags=["Señales"])
app.include_router(whales.router,          prefix="/whales",          tags=["Señales"])

# Market Context
app.include_router(altcoin_season.router,  prefix="/altcoin-season",  tags=["Contexto de mercado"])
app.include_router(market_regime.router,   prefix="/market-regime",   tags=["Contexto de mercado"])
app.include_router(trending.router,        prefix="/trending",        tags=["Contexto de mercado"])
app.include_router(categories.router,      prefix="/categories",      tags=["Contexto de mercado"])

# Derivatives
app.include_router(derivatives.router,     prefix="/derivatives",     tags=["Derivados"])

# Content
app.include_router(news.router,            prefix="/news",            tags=["Contenido"])

# AI
app.include_router(ai.router,              prefix="/ai",              tags=["IA"])

app.include_router(narrative.router,  prefix="/narrative",  tags=["IA y narrativa"])
app.include_router(briefing.router,   prefix="/briefing",   tags=["IA y narrativa"])
app.include_router(alerts.router,     prefix="/alerts",     tags=["Alertas"])

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.get("/", tags=["General"])
def root():
    return {
        "message":  "API de inteligencia CryptoLens",
        "version":  "3.1.0",
        "docs":     "/docs",
        "endpoints": {
            "market":       ["/market/top50", "/market/top20", "/market/history/{symbol}", "/ohlcv/{symbol}", "/ranking", "/performance/{symbol}"],
            "analysis":     ["/analysis/{symbol}", "/analysis/{symbol}/multi-timeframe", "/structure/{symbol}", "/volatility/{symbol}"],
            "signals":      ["/signal/{symbol}", "/whales"],
            "context":      ["/altcoin-season", "/market-regime", "/trending", "/categories"],
            "derivatives":  ["/derivatives/{symbol}"],
            "content":      ["/news"],
            "ai":           ["POST /ai/analyze"]
        }
    }

@app.get("/admin/refresh", tags=["Administración"])
def force_refresh():
    from tasks.scheduler import task_market_data, task_indicators_and_signals, task_whale_activity
    try:
        task_market_data()
        task_whale_activity()
        task_indicators_and_signals()
        return {
            "message": "Datos actualizados",
            "updated": ["market_data", "whale_activity", "indicators", "signals"],
            "updated_labels": ["datos de mercado", "actividad de ballenas", "indicadores", "señales"]
        }
    except Exception as e:
        return {"error": str(e)}
