from fastapi import APIRouter
from services.market_service import fetch_crypto_categories

router = APIRouter()

@router.get("/")
def get_categories():
    return fetch_crypto_categories()