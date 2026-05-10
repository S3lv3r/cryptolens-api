from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from services.ai_service import ask_ai, compare_assets

router = APIRouter()

class AIQuery(BaseModel):
    symbol: str
    query:  str

class AICompare(BaseModel):
    symbols: List[str]
    query:   str

@router.post("/analyze")
def analyze_with_ai(body: AIQuery):
    """
    Análisis de un activo con IA en lenguaje natural.
    La IA usa todos los datos técnicos disponibles del activo.
    """
    if not body.symbol or not body.query:
        raise HTTPException(status_code=400, detail="symbol y query son requeridos")

    result = ask_ai(body.symbol.upper(), body.query)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/compare")
def compare_with_ai(body: AICompare):

    if not body.symbols or not body.query:
        raise HTTPException(status_code=400, detail="symbols y query son requeridos")
    if len(body.symbols) < 2 or len(body.symbols) > 4:
        raise HTTPException(status_code=400, detail="Envía entre 2 y 4 símbolos")

    result = compare_assets(body.symbols, body.query)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result