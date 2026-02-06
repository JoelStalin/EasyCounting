from fastapi import APIRouter, Depends

from app.core.auth import get_current_user

router = APIRouter(prefix="/cliente", tags=["Cliente"])


@router.get("/health")
def health():
    return {"status": "ok", "scope": "cliente"}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"user": user}


@router.get("/facturas")
def listar_facturas(user=Depends(get_current_user)):
    return {"items": [], "owner": user["id"]}


@router.post("/facturas/validar")
def validar_factura(payload: dict, user=Depends(get_current_user)):
    return {"ok": True, "input": payload, "validated_by": user["id"]}
