"""Excepciones personalizadas para getupsoft."""
from __future__ import annotations

from fastapi import HTTPException, status


class TenantNotFoundError(HTTPException):
    """Se lanza cuando no se encuentra un tenant."""

    def __init__(self, tenant_id: int) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant {tenant_id} no encontrado")


class UnauthorizedActionError(HTTPException):
    """Se utiliza para operaciones prohibidas por RBAC."""

    def __init__(self, message: str = "Acción no autorizada") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=message)
