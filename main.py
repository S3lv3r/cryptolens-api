from fastapi import FastAPI
from routers import market, analysis, signals, ranking, whales
from routers import altcoin_season, trending, categories, news, performance
from tasks.scheduler import start_scheduler, task_market_data, task_indicators_and_signals, task_whale_activity
from routers import ohlcv

app = FastAPI(
    title="CryptoLens Intelligence API",
    description="Plataforma SaaS de análisis financiero cripto — Top 50 por market cap",
    version="2.0.0"
)

app.include_router(market.router,         prefix="/market",         tags=["Market"])
app.include_router(analysis.router,       prefix="/analysis",       tags=["Analysis"])
app.include_router(signals.router,        prefix="/signal",         tags=["Signals"])
app.include_router(ranking.router,        prefix="/ranking",        tags=["Ranking"])
app.include_router(whales.router,         prefix="/whales",         tags=["Whales"])
app.include_router(altcoin_season.router, prefix="/altcoin-season", tags=["Altcoin Season"])
app.include_router(trending.router,       prefix="/trending",       tags=["Trending"])
app.include_router(categories.router,     prefix="/categories",     tags=["Categories"])
app.include_router(news.router,           prefix="/news",           tags=["News"])
app.include_router(performance.router,    prefix="/performance",    tags=["Performance"])
app.include_router(ohlcv.router, prefix="/ohlcv", tags=["OHLCV"])

@app.on_event("startup")
async def startup_event():
    start_scheduler()

@app.get("/", tags=["General"])
def root():
    return {
        "message": "CryptoLens Intelligence API",
        "version": "2.0.0",
        "docs": "http://127.0.0.1:8000/docs"
    }

@app.get("/admin/refresh", tags=["Admin"])
def force_refresh():
    try:
        task_market_data()
        task_whale_activity()
        task_indicators_and_signals()
        return {
            "message": "Datos actualizados correctamente",
            "updated": ["market_data", "whale_activity", "indicators", "signals"]
        }
    except Exception as e:
        return {"error": str(e)}