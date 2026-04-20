from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
# Cryptolens11
class Crypto(Base):
    __tablename__ = "cryptos"
    id         = Column(Integer, primary_key=True, index=True)
    symbol     = Column(String(20), unique=True, index=True)
    name       = Column(String(100))
    cmc_id     = Column(Integer, unique=True)
    coingecko_id = Column(String(100), nullable=True)


class MarketData(Base):
    __tablename__ = "market_data"
    id = Column(Integer, primary_key=True, index=True)
    crypto_id = Column(Integer, ForeignKey("cryptos.id"))
    price_usd = Column(Float)
    market_cap = Column(Float)
    volume_24h = Column(Float)
    change_24h = Column(Float)
    change_7d = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    crypto = relationship("Crypto")

class TechnicalIndicator(Base):
    __tablename__ = "technical_indicators"
    id              = Column(Integer, primary_key=True, index=True)
    crypto_id       = Column(Integer, ForeignKey("cryptos.id"))
    ema_9           = Column(Float)
    ema_21          = Column(Float)
    ema_50          = Column(Float)
    lsma_25         = Column(Float, default=0)
    lsma_200        = Column(Float, default=0)
    macd            = Column(Float)
    macd_signal     = Column(Float)
    macd_histogram  = Column(Float)
    rsi             = Column(Float)
    adx             = Column(Float, default=0)
    bb_upper        = Column(Float, default=0)
    bb_middle       = Column(Float, default=0)
    bb_lower        = Column(Float, default=0)
    bb_pct_b        = Column(Float, default=0)
    timestamp       = Column(DateTime, default=datetime.utcnow)
    crypto          = relationship("Crypto")

class Signal(Base):
    __tablename__ = "signals"
    id                  = Column(Integer, primary_key=True, index=True)
    crypto_id           = Column(Integer, ForeignKey("cryptos.id"))
    action              = Column(String(10))
    confidence          = Column(Float)
    explanation         = Column(Text)
    whale_activity      = Column(Text, nullable=True)
    short_term_action   = Column(String(10), nullable=True)
    short_term_risk     = Column(String(20), nullable=True)
    short_term_notes    = Column(Text, nullable=True)
    medium_term_action  = Column(String(10), nullable=True)
    medium_term_notes   = Column(Text, nullable=True)
    long_term_action    = Column(String(10), nullable=True)
    long_term_notes     = Column(Text, nullable=True)
    timestamp           = Column(DateTime, default=datetime.utcnow)
    crypto              = relationship("Crypto")

class WhaleTransaction(Base):
    __tablename__ = "whale_transactions"
    id = Column(Integer, primary_key=True, index=True)
    crypto_id = Column(Integer, ForeignKey("cryptos.id"))
    amount_usd = Column(Float)
    from_wallet = Column(String(200))
    to_wallet = Column(String(200))
    transaction_type = Column(String(50))
    interpretation = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    crypto = relationship("Crypto")