from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

from app.services.dgii_scraper.certification_bot import DGIICertificationBot

logger = logging.getLogger(__name__)

router = APIRouter()

class DGIIStatusRequest(BaseModel):
    rnc: str
    password: str

@router.post("/certification/status", summary="Verificar estado de certificación e-CF en OFV")
async def get_certification_status(request: DGIIStatusRequest):
    """
    Desencadena el bot scraper para consultar el estado actual del 
    contribuyente en la Oficina Virtual de la DGII.
    """
    if not request.rnc or not request.password:
        raise HTTPException(status_code=400, detail="RNC and password are required for OFV access.")
        
    logger.info(f"Received request to check DGII certification for RNC: {request.rnc}")
    
    bot = DGIICertificationBot(rnc=request.rnc, password=request.password)
    
    try:
        result = await bot.check_certification_status()
        return result
    except Exception as e:
        logger.error(f"Failed to check DGII status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
