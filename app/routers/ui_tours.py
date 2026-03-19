from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.portal_deps import get_authenticated_user
from app.models.user import User
from app.services.portal_auth import PortalAuthService
from app.shared.database import get_db

router = APIRouter(prefix="/ui-tours", tags=["UI Tours"])


class UserViewTourItem(BaseModel):
    viewKey: str
    tourVersion: int
    status: str
    lastStep: int | None = None
    completedAt: datetime | None = None


class UserViewTourUpdate(BaseModel):
    tourVersion: int = Field(default=1, ge=1)
    status: str = Field(pattern="^(pending|completed|dismissed)$")
    lastStep: int | None = Field(default=None, ge=0)


@router.get("/me", response_model=list[UserViewTourItem])
def list_my_tours(
    auth: tuple[User, dict] = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
) -> list[UserViewTourItem]:
    user, _payload = auth
    service = PortalAuthService(db)
    tours = service.list_tours(user.id)
    return [
        UserViewTourItem(
            viewKey=tour.view_key,
            tourVersion=tour.tour_version,
            status=tour.status,
            lastStep=tour.last_step,
            completedAt=tour.completed_at,
        )
        for tour in tours
    ]


@router.put("/{view_key}", response_model=UserViewTourItem)
def upsert_my_tour(
    view_key: str,
    payload: UserViewTourUpdate,
    auth: tuple[User, dict] = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
) -> UserViewTourItem:
    user, _token_payload = auth
    service = PortalAuthService(db)
    tour = service.upsert_tour(
        user_id=user.id,
        view_key=view_key,
        tour_version=payload.tourVersion,
        status_value=payload.status,
        last_step=payload.lastStep,
    )
    return UserViewTourItem(
        viewKey=tour.view_key,
        tourVersion=tour.tour_version,
        status=tour.status,
        lastStep=tour.last_step,
        completedAt=tour.completed_at,
    )


@router.post("/{view_key}/reset", response_model=UserViewTourItem)
def reset_my_tour(
    view_key: str,
    auth: tuple[User, dict] = Depends(get_authenticated_user),
    db: Session = Depends(get_db),
) -> UserViewTourItem:
    user, _token_payload = auth
    service = PortalAuthService(db)
    existing = next((tour for tour in service.list_tours(user.id) if tour.view_key == view_key), None)
    version = existing.tour_version if existing else 1
    tour = service.upsert_tour(
        user_id=user.id,
        view_key=view_key,
        tour_version=version,
        status_value="pending",
        last_step=0,
    )
    tour.completed_at = None
    db.flush()
    return UserViewTourItem(
        viewKey=tour.view_key,
        tourVersion=tour.tour_version,
        status=tour.status,
        lastStep=tour.last_step,
        completedAt=tour.completed_at,
    )

