from __future__ import annotations

from typing import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.main import app
from app.models.accounting import TenantSettings
from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.shared.database import get_db
from app.shared.security import create_jwt, hash_password


def _client_with_sqlite() -> tuple[TestClient, sessionmaker]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)
    Base.metadata.create_all(engine)

    def override_get_db() -> Iterator[Session]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), SessionLocal


def test_preliminary_tenant_can_complete_onboarding() -> None:
    client, SessionLocal = _client_with_sqlite()
    with SessionLocal() as session:
        tenant = Tenant(
            name="Empresa Preliminar",
            rnc="99912345678",
            env="PRECERT",
            onboarding_status="pending_fiscal_setup",
            dgii_base_ecf="https://dgii.mock/precert/recepcion",
            dgii_base_fc="https://dgii.mock/precert/rfce",
        )
        session.add(tenant)
        session.flush()
        session.add(
            TenantSettings(
                tenant_id=tenant.id,
                correo_facturacion="pre@getupsoft.com.do",
                telefono_contacto="8095554000",
                notas="Cuenta preliminar",
            )
        )
        user = User(
            tenant_id=tenant.id,
            email="cliente-social@getupsoft.com.do",
            phone="8095554000",
            password_hash=hash_password("Tenant123!"),
            mfa_secret="",
            role="tenant_user",
            status="activo",
        )
        session.add(user)
        session.commit()
        token = create_jwt({"sub": str(user.id), "tenant_id": tenant.id, "role": "tenant_user"})

    headers = {"Authorization": f"Bearer {token}"}
    status_response = client.get("/api/v1/cliente/onboarding", headers=headers)
    assert status_response.status_code == 200
    assert status_response.json()["onboardingStatus"] == "pending_fiscal_setup"

    update = client.put(
        "/api/v1/cliente/onboarding",
        json={
            "companyName": "Empresa Formalizada",
            "rnc": "13141516190",
            "contactEmail": "fiscal@empresa.do",
            "contactPhone": "8095550000",
            "notes": "Setup fiscal completado",
        },
        headers=headers,
    )
    app.dependency_overrides.clear()
    assert update.status_code == 200
    body = update.json()
    assert body["onboardingStatus"] == "completed"
    assert body["canEmitReal"] is True
    assert body["rnc"] == "13141516190"
