from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import MarketData, Crypto
from services.altcoin_season_service import calculate_altcoin_season_index
from services.market_service import fetch_top_cryptos

router = APIRouter()

@router.get("/")
def get_altcoin_season():
    top20 = fetch_top_cryptos(limit=50)
    return calculate_altcoin_season_index(top20)