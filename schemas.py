from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MarketDataOut(BaseModel):
    symbol: str
    name: str
    price_usd: float
    market_cap: float
    volume_24h: float
    change_24h: float
    change_7d: float
    timestamp: datetime

    class Config:
        from_attributes = True

class IndicatorOut(BaseModel):
    symbol: str
    ema_9: float
    ema_21: float
    ema_50: float
    macd: float
    macd_signal: float
    macd_histogram: float
    rsi: float
    timestamp: datetime

    class Config:
        from_attributes = True

class HorizonSignal(BaseModel):
    horizon: str
    notes: str
    risk: Optional[str] = None

class SignalHorizons(BaseModel):
    short_term: HorizonSignal
    medium_term: HorizonSignal
    long_term: HorizonSignal

class SignalOut(BaseModel):
    symbol: str
    action: str
    confidence: float
    explanation: str
    whale_activity: Optional[str] = None
    horizons: Optional[SignalHorizons] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class WhaleOut(BaseModel):
    symbol: str
    amount_usd: float
    from_wallet: str
    to_wallet: str
    transaction_type: str
    interpretation: str
    timestamp: datetime

    class Config:
        from_attributes = True

class RankingItem(BaseModel):
    rank: int
    symbol: str
    name: str
    price_usd: float
    market_cap: float
    change_24h: float
    signal: Optional[str] = None