"""Application settings module."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import List, Literal, Set

from pydantic import AliasChoices, AnyUrl, Field, computed_field, constr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    """Centralised configuration for the DGII service."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=True, env_ignore_empty=True)

    app_name: str = Field(default="DGII e-CF API")
    environment: constr(strip_whitespace=True) = Field(default="development")

    cors_allow_origins_raw: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CORS_ALLOW_ORIGINS", "FRONTEND_ORIGINS"),
    )
    rate_limit_per_minute: int = Field(default=100, ge=1)

    jwt_secret: str = Field(default="change-me", validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"))
    jwt_access_exp_minutes: int = Field(default=15, ge=5, le=60, validation_alias=AliasChoices("JWT_ACCESS_EXP_MINUTES", "ACCESS_TOKEN_EXP_MINUTES"))
    refresh_token_exp_minutes: int = Field(default=60 * 24 * 7, validation_alias=AliasChoices("REFRESH_TOKEN_EXP_MINUTES", "JWT_REFRESH_EXP_MINUTES"))
    mfa_enabled: bool = Field(default=False, validation_alias=AliasChoices("MFA_ENABLED"))

    bootstrap_admin_email: str = Field(
        default="admin@getupsoft.local",
        validation_alias=AliasChoices("BOOTSTRAP_ADMIN_EMAIL"),
    )
    bootstrap_admin_password: str = Field(
        default="ChangeMe123!",
        validation_alias=AliasChoices("BOOTSTRAP_ADMIN_PASSWORD"),
    )
    bootstrap_admin_role: str = Field(
        default="platform_admin",
        validation_alias=AliasChoices("BOOTSTRAP_ADMIN_ROLE"),
    )
    bootstrap_admin_phone: str = Field(
        default="0000000000",
        validation_alias=AliasChoices("BOOTSTRAP_ADMIN_PHONE"),
    )

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/dgii",
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_DSN"),
    )
    redis_url: str = Field(default="redis://localhost:6379/0")
    sentry_dsn: str | None = Field(default=None)
    sentry_traces_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0, alias="SENTRY_TRACES")

    dgii_env: Literal["PRECERT", "CERT", "PROD"] = Field(default="PRECERT", validation_alias=AliasChoices("DGII_ENV", "ENV"))
    dgii_allowed_hosts_raw: str | None = Field(default=None, validation_alias=AliasChoices("DGII_ALLOWED_HOSTS"))

    # Official DGII services (base URLs by environment)
    dgii_auth_base_url_precert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/TesteCF/Autenticacion",
        validation_alias=AliasChoices("DGII_AUTH_BASE_URL_PRECERT"),
    )
    dgii_auth_base_url_cert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/CerteCF/Autenticacion",
        validation_alias=AliasChoices("DGII_AUTH_BASE_URL_CERT"),
    )
    dgii_auth_base_url_prod: AnyUrl = Field(
        "https://ecf.dgii.gov.do/ecf/autenticacion",
        validation_alias=AliasChoices("DGII_AUTH_BASE_URL_PROD"),
    )

    dgii_recepcion_base_url_precert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/TesteCF/Recepcion",
        validation_alias=AliasChoices("DGII_RECEPCION_BASE_URL_PRECERT"),
    )
    dgii_recepcion_base_url_cert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/CerteCF/Recepcion",
        validation_alias=AliasChoices("DGII_RECEPCION_BASE_URL_CERT"),
    )
    dgii_recepcion_base_url_prod: AnyUrl = Field(
        "https://ecf.dgii.gov.do/eCF/Recepcion",
        validation_alias=AliasChoices("DGII_RECEPCION_BASE_URL_PROD"),
    )

    dgii_recepcion_fc_base_url_precert: AnyUrl = Field(
        "https://fc.dgii.gov.do/testecf/recepcionfc",
        validation_alias=AliasChoices("DGII_RECEPCION_FC_BASE_URL_PRECERT"),
    )
    dgii_recepcion_fc_base_url_cert: AnyUrl = Field(
        "https://fc.dgii.gov.do/certecf/recepcionfc",
        validation_alias=AliasChoices("DGII_RECEPCION_FC_BASE_URL_CERT"),
    )
    dgii_recepcion_fc_base_url_prod: AnyUrl = Field(
        "https://fc.dgii.gov.do/ecf/recepcionfc",
        validation_alias=AliasChoices("DGII_RECEPCION_FC_BASE_URL_PROD"),
    )

    dgii_consulta_estado_base_url_precert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/testecf/consultaestado",
        validation_alias=AliasChoices("DGII_CONSULTA_ESTADO_BASE_URL_PRECERT"),
    )
    dgii_consulta_estado_base_url_prod: AnyUrl = Field(
        "https://ecf.dgii.gov.do/ecf/consultaestado",
        validation_alias=AliasChoices("DGII_CONSULTA_ESTADO_BASE_URL_PROD"),
    )

    dgii_consulta_trackids_base_url_precert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/testecf/consultatrackids",
        validation_alias=AliasChoices("DGII_CONSULTA_TRACKIDS_BASE_URL_PRECERT"),
    )
    dgii_consulta_trackids_base_url_prod: AnyUrl = Field(
        "https://ecf.dgii.gov.do/ecf/consultatrackids",
        validation_alias=AliasChoices("DGII_CONSULTA_TRACKIDS_BASE_URL_PROD"),
    )

    dgii_consulta_directorio_base_url_precert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/testecf/consultadirectorio",
        validation_alias=AliasChoices("DGII_CONSULTA_DIRECTORIO_BASE_URL_PRECERT"),
    )
    dgii_consulta_directorio_base_url_prod: AnyUrl = Field(
        "https://ecf.dgii.gov.do/ecf/consultadirectorio",
        validation_alias=AliasChoices("DGII_CONSULTA_DIRECTORIO_BASE_URL_PROD"),
    )

    dgii_consulta_resultado_base_url_precert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/TesteCF/ConsultaResultado",
        validation_alias=AliasChoices("DGII_CONSULTA_RESULTADO_BASE_URL_PRECERT"),
    )
    dgii_consulta_resultado_base_url_cert: AnyUrl = Field(
        "https://ecf.dgii.gov.do/CerteCF/ConsultaResultado",
        validation_alias=AliasChoices("DGII_CONSULTA_RESULTADO_BASE_URL_CERT"),
    )
    dgii_consulta_resultado_base_url_prod: AnyUrl = Field(
        "https://ecf.dgii.gov.do/eCF/ConsultaResultado",
        validation_alias=AliasChoices("DGII_CONSULTA_RESULTADO_BASE_URL_PROD"),
    )

    dgii_timeout: float = Field(default=5.0, gt=0)
    dgii_conn_timeout: float = Field(default=2.0, gt=0)
    dgii_max_retries: int = Field(default=3, ge=0)
    dgii_circuit_breaker_threshold: int = Field(default=5, ge=1)
    dgii_circuit_breaker_window: int = Field(default=60, ge=1)

    dgii_p12_path: str = Field(default="/secrets/cert.p12")
    dgii_p12_password: str = Field(default="changeit")

    enfc_require_bearer_token: bool = Field(default=False, validation_alias=AliasChoices("ENFC_REQUIRE_BEARER_TOKEN"))
    enfc_token_ttl_seconds: int = Field(default=900, ge=60, le=86400, validation_alias=AliasChoices("ENFC_TOKEN_TTL_SECONDS"))
    enfc_require_x509_signature: bool = Field(default=False, validation_alias=AliasChoices("ENFC_REQUIRE_X509_SIGNATURE"))

    @staticmethod
    def _parse_csv_or_json_array(value: str) -> list[str]:
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError:
                decoded = None
            if isinstance(decoded, list):
                return [str(item).strip() for item in decoded if str(item).strip()]
        return [item.strip() for item in stripped.split(",") if item.strip()]

    @computed_field
    @property
    def cors_allow_origins(self) -> List[str]:
        if self.cors_allow_origins_raw is None:
            return [
                "https://api.dgii.getupsoft.com.do",
                "https://staging.dgii.getupsoft.com.do",
            ]
        return self._parse_csv_or_json_array(self.cors_allow_origins_raw)

    @computed_field
    @property
    def dgii_allowed_hosts(self) -> Set[str]:
        if self.dgii_allowed_hosts_raw is None:
            return {
                "ecf.dgii.gov.do",
                "fc.dgii.gov.do",
                "servicios.dgii.gov.do",
                "eCF.dgii.gov.do",
            }
        return set(self._parse_csv_or_json_array(self.dgii_allowed_hosts_raw))

    @computed_field
    @property
    def secret_key(self) -> str:
        return self.jwt_secret

    @computed_field
    @property
    def access_token_exp_minutes(self) -> int:
        return self.jwt_access_exp_minutes

    @computed_field
    @property
    def dgii_auth_base_url(self) -> str:
        if self.dgii_env == "PRECERT":
            return str(self.dgii_auth_base_url_precert)
        if self.dgii_env == "CERT":
            return str(self.dgii_auth_base_url_cert)
        return str(self.dgii_auth_base_url_prod)

    @computed_field
    @property
    def dgii_recepcion_base_url(self) -> str:
        if self.dgii_env == "PRECERT":
            return str(self.dgii_recepcion_base_url_precert)
        if self.dgii_env == "CERT":
            return str(self.dgii_recepcion_base_url_cert)
        return str(self.dgii_recepcion_base_url_prod)

    @computed_field
    @property
    def dgii_recepcion_fc_base_url(self) -> str:
        if self.dgii_env == "PRECERT":
            return str(self.dgii_recepcion_fc_base_url_precert)
        if self.dgii_env == "CERT":
            return str(self.dgii_recepcion_fc_base_url_cert)
        return str(self.dgii_recepcion_fc_base_url_prod)

    @computed_field
    @property
    def dgii_consulta_estado_base_url(self) -> str:
        if self.dgii_env == "PROD":
            return str(self.dgii_consulta_estado_base_url_prod)
        return str(self.dgii_consulta_estado_base_url_precert)

    @computed_field
    @property
    def dgii_consulta_trackids_base_url(self) -> str:
        if self.dgii_env == "PROD":
            return str(self.dgii_consulta_trackids_base_url_prod)
        return str(self.dgii_consulta_trackids_base_url_precert)

    @computed_field
    @property
    def dgii_consulta_directorio_base_url(self) -> str:
        if self.dgii_env == "PROD":
            return str(self.dgii_consulta_directorio_base_url_prod)
        return str(self.dgii_consulta_directorio_base_url_precert)

    @computed_field
    @property
    def dgii_consulta_resultado_base_url(self) -> str:
        if self.dgii_env == "PRECERT":
            return str(self.dgii_consulta_resultado_base_url_precert)
        if self.dgii_env == "CERT":
            return str(self.dgii_consulta_resultado_base_url_cert)
        return str(self.dgii_consulta_resultado_base_url_prod)

    @computed_field
    @property
    def sqlalchemy_async_url(self) -> str:
        """Ensure the SQLAlchemy URL uses an async driver."""

        url = make_url(self.database_url)
        if url.drivername.endswith("+asyncpg"):
            return self.database_url

        if "+" in url.drivername:
            dialect, _driver = url.drivername.split("+", 1)
        else:
            dialect = url.drivername

        async_url = url.set(drivername=f"{dialect}+asyncpg")
        return async_url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
