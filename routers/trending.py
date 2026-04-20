from fastapi import APIRouter
from services.market_service import fetch_trending_latest

router = APIRouter()

@router.get("/")
def get_trending():
    return fetch_trending_latest()