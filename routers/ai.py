from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ai_service import ask_ai

router = APIRouter()

class AIQuery(BaseModel):
    symbol: str
    query:  str

@router.post("/analyze")
def analyze_with_ai(body: AIQuery):
    """
    Análisis de mercado con IA (Groq/Llama3).
    Envía los datos técnicos del activo + tu pregunta y la IA responde en lenguaje natural.

    Ejemplo:
    {
        "symbol": "XLM",
        "query": "Analiza XLM estos últimos días y dime cómo está el mercado"
    }
    """
    if not body.symbol or not body.query:
        raise HTTPException(status_code=400, detail="symbol y query son requeridos")

    result = ask_ai(body.symbol.upper(), body.query)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result