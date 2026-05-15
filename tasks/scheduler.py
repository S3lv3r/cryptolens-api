from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from models import Crypto, MarketData, TechnicalIndicator, Signal, WhaleTransaction
from services.market_service import (
    fetch_top_cryptos,
    fetch_price_history,
    fetch_ohlcv_history,
    fetch_trending_latest
)
from services.technical_service import (
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_lsma,
    calculate_bollinger_bands,
    calculate_adx_ohlcv
)
from services.signal_service import generate_signal
from services.whale_service import fetch_whale_events_batch, interpret_whale_transaction
from services.binance_service import fetch_klines

def task_market_data():
    db = SessionLocal()
    try:
        data = fetch_top_cryptos(limit=50)
        print(f"CMC devolvió {len(data)} cryptos")

        for item in data:
            cmc_id = item["id"]
            crypto = db.query(Crypto).filter(Crypto.cmc_id == cmc_id).first()
            if not crypto:
                print(f"{item['symbol']} no está en DB")
                continue

            quote = item["quote"]["USD"]
            market = MarketData(
                crypto_id=crypto.id,
                price_usd=quote["price"],
                market_cap=quote["market_cap"],
                volume_24h=quote["volume_24h"],
                change_24h=quote.get("percent_change_24h", 0),
                change_7d=quote.get("percent_change_7d", 0)
            )
            db.add(market)
            print(f"{crypto.symbol}: ${quote['price']:,.2f}")

        db.commit()
        print(" Datos de mercado actualizados")

    except Exception as e:
        print(f" Error en task_market_data: {e}")
        db.rollback()
    finally:
        db.close()


def task_indicators_and_signals():
    db = SessionLocal()
    cryptos = db.query(Crypto).all()
    crypto_list = [(c.id, c.symbol, c.cmc_id) for c in cryptos]
    db.close()

    for crypto_id, symbol, cmc_id in crypto_list:
        db = SessionLocal()
        try:
            print(f"Obteniendo historial de {symbol}...")

            klines = fetch_klines(symbol, timeframe="1d", limit=250)

            if klines and len(klines) >= 200:
                print(f"{symbol}: Usando datos de Binance ({len(klines)} velas)")
                prices = [k["close"] for k in klines]
                ohlcv = klines
            else:
                print(f"{symbol}: Binance falló/datos insuficientes. Usando CMC...")
                prices = fetch_price_history(cmc_id, days=250)
                ohlcv = fetch_ohlcv_history(cmc_id, days=250)

            if len(prices) < 26 or len(ohlcv) < 14:
                print(f"{symbol}: Datos insuficientes en ambas fuentes. Saltando...")
                db.close()
                continue
            

            macd_data = calculate_macd(prices)
            ema_9     = calculate_ema(prices, 9)
            ema_21    = calculate_ema(prices, 21)
            ema_50    = calculate_ema(prices, 50) if len(prices) >= 50 else 0
            rsi       = calculate_rsi(prices)
            lsma_25   = calculate_lsma(prices, 25)
            
            lsma_200  = calculate_lsma(prices, 200) if len(prices) >= 200 else 0

            bb        = calculate_bollinger_bands(prices)

            highs  = [c["high"]  for c in ohlcv]
            lows   = [c["low"]   for c in ohlcv]
            closes = [c["close"] for c in ohlcv]
            adx_data = calculate_adx_ohlcv(highs, lows, closes)

            indicator = TechnicalIndicator(
                crypto_id      = crypto_id,
                ema_9          = ema_9,
                ema_21         = ema_21,
                ema_50         = ema_50,
                lsma_25        = lsma_25,
                lsma_200       = lsma_200,
                macd           = macd_data["macd"],
                macd_signal    = macd_data["signal"],
                macd_histogram = macd_data["histogram"],
                rsi            = rsi,
                adx            = adx_data["adx"],
                bb_upper       = bb["upper"],
                bb_middle      = bb["middle"],
                bb_lower       = bb["lower"],
                bb_pct_b       = bb["pct_b"]
            )
            db.add(indicator)

            latest_price = prices[-1]

            signal_data = generate_signal(
                rsi        = rsi,
                macd       = macd_data["macd"],
                macd_signal= macd_data["signal"],
                ema_9      = ema_9,
                ema_21     = ema_21,
                lsma_25    = lsma_25,
                lsma_200   = lsma_200,
                adx        = adx_data["adx"],
                bb_pct_b   = bb["pct_b"],
                price      = latest_price
            )
            
            signal = Signal(
                crypto_id=crypto_id,
                action=signal_data["action"],
                confidence=signal_data["confidence"],
                explanation=signal_data["explanation"],
                whale_activity=signal_data.get("whale_activity"),
                short_term_action=signal_data["horizons"]["short_term"].get("action", signal_data["action"]),
                short_term_risk=signal_data["horizons"]["short_term"].get("risk", "medio"),
                short_term_notes=signal_data["horizons"]["short_term"].get("notes", ""),
                medium_term_action=signal_data["horizons"]["medium_term"].get("action", signal_data["action"]),
                medium_term_notes=signal_data["horizons"]["medium_term"].get("notes", ""),
                long_term_action=signal_data["horizons"]["long_term"].get("action", signal_data["action"]),
                long_term_notes=signal_data["horizons"]["long_term"].get("notes", ""),
            )
            db.add(signal)
            db.commit()
            print(f"{symbol}: {signal_data['action']} | RSI:{rsi} ADX:{adx_data['adx']} LSMA200:{lsma_200}")

        except Exception as e:
            print(f"{symbol}: Error procesando indicadores: {e}")
            db.rollback()
        finally:
            db.close()

def task_whale_activity():
    db = SessionLocal()
    try:
        events = fetch_whale_events_batch()

        saved = 0
        for event in events:
            crypto = db.query(Crypto).filter(
                Crypto.symbol == event["symbol"]
            ).first()

            if not crypto:
                continue

            whale = WhaleTransaction(
                crypto_id       = crypto.id,
                amount_usd      = event["amount_usd"],
                from_wallet     = event["from_wallet"],
                to_wallet       = event["to_wallet"],
                transaction_type= event["transaction_type"],
                interpretation  = event["interpretation"]
            )
            db.add(whale)
            saved += 1

        db.commit()
        print(f"{saved} eventos de ballenas guardados en DB")

    except Exception as e:
        print(f"Error en task_whale_activity: {e}")
        db.rollback()
    finally:
        db.close()

def task_trending():
    try:
        data = fetch_trending_latest()
        gainers = [c["symbol"] for c in data.get("gainers", [])]
        losers  = [c["symbol"] for c in data.get("losers", [])]
        print(f"Gainers: {gainers}")
        print(f"Losers: {losers}")
    except Exception as e:
        print(f"Error en task_trending: {e}")

def task_scan_alerts():
    from database import SessionLocal
    from models import Crypto
    from services.alert_service import detect_alerts_for_symbol

    db = SessionLocal()
    cryptos = db.query(Crypto).all()
    db.close()

    total_alerts = 0
    for crypto in cryptos:
        try:
            alerts = detect_alerts_for_symbol(crypto.symbol)
            total_alerts += len(alerts)
        except Exception as e:
            print(f" Alert scan {crypto.symbol}: {e}")
            continue

    print(f"Scan completado: {total_alerts} alertas detectadas en {len(cryptos)} activos")



def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(task_market_data,            "interval", minutes=5,   id="market")
    scheduler.add_job(task_indicators_and_signals, "interval", minutes=30,  id="indicators")
    scheduler.add_job(task_whale_activity,         "interval", hours=1,     id="whales")
    scheduler.add_job(task_trending,               "interval", minutes=30,  id="trending")
    scheduler.add_job(task_scan_alerts, "interval", minutes=15, id="alerts")
    scheduler.start()
    print("Scheduler iniciado")