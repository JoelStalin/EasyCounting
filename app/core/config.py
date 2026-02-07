"""Core application settings and helpers."""
from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DGIIEnvironment(str, Enum):
    """Supported DGII environments."""

    PRECERT = "PRECERT"
    CERT = "CERT"
    PROD = "PROD"


class Settings(BaseSettings):
    """Global application settings resolved from environment variables."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env.development",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General application configuration
    app_name: str = Field("getupsoft API", description="Nombre expuesto en OpenAPI")
    environment: str = Field("development", description="Entorno de despliegue actual")
    secret_key: str = Field("dev-secret", validation_alias=AliasChoices("JWT_SECRET"), description="Secreto para firmar JWT")
    hmac_service_secret: str = Field("dev-hmac", validation_alias=AliasChoices("HMAC_SERVICE_SECRET"), description="Secreto compartido entre microservicios")
    access_token_exp_minutes: int = Field(15, ge=5, le=120, description="Duración del access token en minutos")
    refresh_token_exp_minutes: int = Field(60 * 24 * 7, description="Duración del refresh token en minutos")
    database_url: str = Field("sqlite:///./local.db", validation_alias=AliasChoices("DB_URL"), description="Cadena de conexión a PostgreSQL/SQLite")
    redis_url: str = Field("redis://localhost:6379/0", validation_alias=AliasChoices("REDIS_URL"), description="URL de conexión a Redis")
    log_level: str = Field("INFO", description="Nivel de logs para toda la plataforma")
    cors_allow_origins: List[str] = Field(default_factory=list, description="Orígenes permitidos para CORS")
    tls_enabled: bool = Field(True, description="Indica si el despliegue debe forzar TLS 1.3")
    tracing_header: str = Field("X-Trace-ID", description="Encabezado utilizado para el tracing distribuido")
    request_id_header: str = Field("X-Request-ID", description="Encabezado de correlación de solicitudes")
    metrics_enabled: bool = Field(True, description="Habilita la exposición de métricas Prometheus")
    sentry_dsn: Optional[str] = Field(None, validation_alias=AliasChoices("SENTRY_DSN"), description="DSN de Sentry opcional")
    storage_bucket: str = Field("local", description="Bucket/espacio para almacenamiento WORM")
    storage_base_path: Path = Field(Path("/var/getupsoft/storage"), description="Ruta por defecto para almacenamiento local")

    # DGII specific configuration
    env: DGIIEnvironment = Field(DGIIEnvironment.PRECERT, alias="ENV", description="Ambiente DGII activo")
    dgii_auth_base_url_precert: AnyUrl = Field("https://dgii.mock/precert/auth", alias="DGII_AUTH_BASE_URL_PRECERT")
    dgii_auth_base_url_cert: AnyUrl = Field("https://dgii.mock/cert/auth", alias="DGII_AUTH_BASE_URL_CERT")
    dgii_auth_base_url_prod: AnyUrl = Field("https://dgii.mock/prod/auth", alias="DGII_AUTH_BASE_URL_PROD")

    dgii_recepcion_base_url_precert: AnyUrl = Field("https://dgii.mock/precert/recepcion", alias="DGII_RECEPCION_BASE_URL_PRECERT")
    dgii_recepcion_base_url_cert: AnyUrl = Field("https://dgii.mock/cert/recepcion", alias="DGII_RECEPCION_BASE_URL_CERT")
    dgii_recepcion_base_url_prod: AnyUrl = Field("https://dgii.mock/prod/recepcion", alias="DGII_RECEPCION_BASE_URL_PROD")

    dgii_recepcion_fc_base_url_precert: AnyUrl = Field("https://dgii.mock/precert/rfce", alias="DGII_RECEPCION_FC_BASE_URL_PRECERT")
    dgii_recepcion_fc_base_url_cert: AnyUrl = Field("https://dgii.mock/cert/rfce", alias="DGII_RECEPCION_FC_BASE_URL_CERT")
    dgii_recepcion_fc_base_url_prod: AnyUrl = Field("https://dgii.mock/prod/rfce", alias="DGII_RECEPCION_FC_BASE_URL_PROD")

    dgii_directorio_base_url_precert: AnyUrl = Field("https://dgii.mock/precert/directorio", alias="DGII_DIRECTORIO_BASE_URL_PRECERT")
    dgii_directorio_base_url_cert: AnyUrl = Field("https://dgii.mock/cert/directorio", alias="DGII_DIRECTORIO_BASE_URL_CERT")
    dgii_directorio_base_url_prod: AnyUrl = Field("https://dgii.mock/prod/directorio", alias="DGII_DIRECTORIO_BASE_URL_PROD")

    dgii_rnc: str = Field("131415161", alias="DGII_RNC")
    dgii_cert_p12_path: Path = Field(Path("/secrets/company_cert.p12"), alias="DGII_CERT_P12_PATH")
    dgii_cert_p12_password: str = Field("changeit", alias="DGII_CERT_P12_PASSWORD")
    dgii_http_timeout_seconds: int = Field(30, alias="DGII_HTTP_TIMEOUT_SECONDS", ge=5, le=120)
    dgii_http_retries: int = Field(3, alias="DGII_HTTP_RETRIES", ge=0, le=5)
    ri_qr_base_url: AnyUrl = Field("https://ri.mock/qr", alias="RI_QR_BASE_URL")

    # Feature flags / background jobs
    jobs_enabled: bool = Field(True, description="Permite ejecutar tareas internas para reintentos")

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return value
        return [origin.strip() for origin in value.split(",") if origin.strip()] if value else []

    def resolve_service_urls(self) -> Dict[str, str]:
        """Return the base URLs for the active DGII environment."""

        env = self.env
        mapping: Dict[str, Dict[DGIIEnvironment, AnyUrl]] = {
            "auth": {
                DGIIEnvironment.PRECERT: self.dgii_auth_base_url_precert,
                DGIIEnvironment.CERT: self.dgii_auth_base_url_cert,
                DGIIEnvironment.PROD: self.dgii_auth_base_url_prod,
            },
            "recepcion": {
                DGIIEnvironment.PRECERT: self.dgii_recepcion_base_url_precert,
                DGIIEnvironment.CERT: self.dgii_recepcion_base_url_cert,
                DGIIEnvironment.PROD: self.dgii_recepcion_base_url_prod,
            },
            "recepcion_fc": {
                DGIIEnvironment.PRECERT: self.dgii_recepcion_fc_base_url_precert,
                DGIIEnvironment.CERT: self.dgii_recepcion_fc_base_url_cert,
                DGIIEnvironment.PROD: self.dgii_recepcion_fc_base_url_prod,
            },
            "directorio": {
                DGIIEnvironment.PRECERT: self.dgii_directorio_base_url_precert,
                DGIIEnvironment.CERT: self.dgii_directorio_base_url_cert,
                DGIIEnvironment.PROD: self.dgii_directorio_base_url_prod,
            },
        }
        return {key: value[env] for key, value in mapping.items()}

    def url_for(self, service: str, env: Optional[DGIIEnvironment] = None) -> str:
        """Return the base URL for the given DGII service."""

        resolved_env = env or self.env
        env_urls = {
            DGIIEnvironment.PRECERT: {
                "auth": self.dgii_auth_base_url_precert,
                "recepcion": self.dgii_recepcion_base_url_precert,
                "recepcion_fc": self.dgii_recepcion_fc_base_url_precert,
                "directorio": self.dgii_directorio_base_url_precert,
            },
            DGIIEnvironment.CERT: {
                "auth": self.dgii_auth_base_url_cert,
                "recepcion": self.dgii_recepcion_base_url_cert,
                "recepcion_fc": self.dgii_recepcion_fc_base_url_cert,
                "directorio": self.dgii_directorio_base_url_cert,
            },
            DGIIEnvironment.PROD: {
                "auth": self.dgii_auth_base_url_prod,
                "recepcion": self.dgii_recepcion_base_url_prod,
                "recepcion_fc": self.dgii_recepcion_fc_base_url_prod,
                "directorio": self.dgii_directorio_base_url_prod,
            },
        }
        try:
            return env_urls[resolved_env][service]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise KeyError(f"Servicio DGII desconocido: {service}") from exc


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
