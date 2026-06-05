# CryptoLens API | Financial Intelligence Analytics Backend

A robust Python/FastAPI backend designed to centralize cryptocurrency market telemetry, compute technical indicators, generate trading signals, and expose AI-driven market narratives for client applications.

This project is built as an analytical engine for UIs or external services. It does not attempt to be an execution platform, a wallet, or a high-frequency trading bot. Instead, it aggregates third-party data, persists it, processes complex mathematical metrics, and returns structured data payloads for decoupled frontends.

## Core Features & Engineering Highlights

* **Graceful Degradation (Local Fallback):** Implements a robust fallback service. If upstream providers (e.g., CoinMarketCap) hit rate limits or go offline, the API seamlessly switches to serving the latest cached snapshots from the local database, marking the payload with `_source: "local_database"` to ensure UI continuity.
* **Dual-Layer Architecture:** Separates the asynchronous data collection (via APScheduler cron jobs) from the API exposure layer (FastAPI routers).
* **AI Integration:** Utilizes the Groq API (LLaMA 3) to process raw database metrics into natural language market briefings, anomaly explanations, and narrative comparisons.
* **Algorithmic Analysis:** Computes real-time RSI, MACD, EMA, ADX, Bollinger Bands, and LSMA using Pandas and NumPy.
* **Stable UI Contracts:** Exposes technical English keys (`action: "BUY"`) alongside localized UI-ready labels (`action_label: "Comprar"`) to prevent frontend breaking changes.

## System Architecture

~~~mermaid
flowchart TD
    subgraph Data Collection Layer
        Cron[APScheduler Background Tasks]
        CMC[CoinMarketCap API]
        Binance[Binance Public API]
        
        Cron -->|Fetch 5m/30m/1h| CMC
        Cron -->|Fetch Derivatives| Binance
    end

    subgraph Persistence Layer
        DB[(MySQL Database)]
        Cron -->|Save Snapshots| DB
    end

    subgraph API Exposure Layer
        FastAPI[FastAPI Routers]
        Groq[Groq AI Engine]
        
        FastAPI <-->|Query Data| DB
        FastAPI <-->|Generate Narratives| Groq
    end

    subgraph Client
        UI[React / Flutter Apps]
        UI -->|HTTP GET/POST| FastAPI
    end
~~~

## Tech Stack

* **Framework:** Python, FastAPI
* **Database & ORM:** MySQL, PyMySQL, SQLAlchemy
* **Data Processing:** Pandas, NumPy
* **Task Scheduling:** APScheduler
* **External APIs:** CoinMarketCap, Binance Futures, Groq AI
* **Environment:** python-dotenv, Uvicorn

## Core Endpoints Overview

The API is structured into modular routers. Interactive documentation is available locally via Swagger UI at `/docs`.

| Category | Endpoints | Description |
| :--- | :--- | :--- |
| **Market** | `/market/top50`, `/ohlcv/{symbol}` | Core pricing, market cap, and historical candle data (with DB fallback). |
| **Technical** | `/analysis/{symbol}`, `/structure/{symbol}` | Indicator calculations and market structure (BOS, CHOCH, Support/Resistance). |
| **Signals** | `/signal/{symbol}`, `/alerts/scan/all` | Actionable signals with confidence scores and extreme volume alerts (Whales). |
| **Context** | `/altcoin-season`, `/market-regime` | Global market classification (e.g., Accumulation, Distribution). |
| **AI Content** | `/ai/analyze`, `/briefing/{context}` | Groq-generated natural language market summaries and asset comparisons. |

## Local Setup & Development

1. Create and activate a virtual environment:
~~~bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
~~~

2. Install dependencies:
~~~bash
pip install -r requirements.txt
~~~

3. Copy `.env.example` to `.env` and populate your API keys (Database, Groq, CoinMarketCap).

4. Initialize the database schema:
~~~bash
python init_db.py
~~~

5. Run the development server:
~~~bash
uvicorn main:app --reload
~~~

## Technical Debt & Known Limitations

As an evolving analytical engine, the following architectural compromises are acknowledged:
* **Coupled Scheduler:** APScheduler currently runs within the same process as the FastAPI app. For high-load production environments, the worker layer should be extracted into a separate service (e.g., Celery/Redis).
* **Approximate Fallback OHLCV:** When the upstream provider fails, the local DB fallback reconstructs an approximate daily candle using the stored spot price for `open`, `high`, `low`, and `close`.
* **Testing Coverage:** Lacks a formalized automated testing suite (pytest) for the mathematical indicator calculation layer.
* **Disclaimer:** Signals are pure technical interpretations and do not constitute guaranteed financial advice.

## License
MIT