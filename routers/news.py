from fastapi import APIRouter
from services.market_service import fetch_news

router = APIRouter()

@router.get("/")
def get_news():
    return fetch_news()