from fastapi import APIRouter, HTTPException
from services.briefing_service import generate_briefing

router = APIRouter()

VALID_CONTEXTS = ["morning", "evening", "weekly", "alert"]
CONTEXT_HELP = {
    "morning": "morning (matutino)",
    "evening": "evening (vespertino)",
    "weekly": "weekly (semanal)",
    "alert": "alert (alerta)"
}

@router.get("/{context}")
def get_briefing(context: str):
    """
    Briefing de mercado generado con IA según el contexto.

    Contextos disponibles:
    - morning → qué pasó mientras dormías, cómo arrancar el día
    - evening → resumen del día, qué vigilar esta noche
    - weekly  → resumen semanal y outlook próxima semana
    - alert   → condiciones urgentes ahora mismo

    Se cachea automáticamente según el contexto.
    """
    if context not in VALID_CONTEXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Contexto inválido. Usa: {', '.join(CONTEXT_HELP[c] for c in VALID_CONTEXTS)}"
        )

    result = generate_briefing(context)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result
