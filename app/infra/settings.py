"""Application settings module."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Set

from pydantic import AliasChoices, AnyUrl, Field, computed_field, constr, field_validator, model_validator
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
    client_portal_domain: str = Field(
        default="cliente.getupsoft.com.do",
        validation_alias=AliasChoices("CLIENT_PORTAL_DOMAIN"),
    )
    app_portal_domain: str = Field(
        default="app.getupsoft.com.do",
        validation_alias=AliasChoices("APP_PORTAL_DOMAIN"),
    )
    admin_portal_domain: str = Field(
        default="admin.getupsoft.com.do",
        validation_alias=AliasChoices("ADMIN_PORTAL_DOMAIN"),
    )
    partner_portal_domain: str = Field(
        default="socios.getupsoft.com.do",
        validation_alias=AliasChoices("PARTNER_PORTAL_DOMAIN", "SELLER_PORTAL_DOMAIN"),
    )
    public_site_domain: str = Field(
        default="www.getupsoft.com.do",
        validation_alias=AliasChoices("PUBLIC_SITE_DOMAIN", "CORPORATE_PORTAL_DOMAIN"),
    )
    rate_limit_per_minute: int = Field(default=100, ge=1)

    jwt_secret: str = Field(default="change-me", validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY"))
    jwt_access_exp_minutes: int = Field(default=15, ge=5, le=60, validation_alias=AliasChoices("JWT_ACCESS_EXP_MINUTES", "ACCESS_TOKEN_EXP_MINUTES"))
    refresh_token_exp_minutes: int = Field(default=60 * 24 * 7, validation_alias=AliasChoices("REFRESH_TOKEN_EXP_MINUTES", "JWT_REFRESH_EXP_MINUTES"))
    mfa_enabled: bool = Field(default=False, validation_alias=AliasChoices("MFA_ENABLED"))
    compat_api_enabled: bool = Field(default=True, validation_alias=AliasChoices("COMPAT_API_ENABLED"))
    hmac_service_secret: str = Field(default="dev-hmac", validation_alias=AliasChoices("HMAC_SERVICE_SECRET"))
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL"))
    tls_enabled: bool = Field(default=True, validation_alias=AliasChoices("TLS_ENABLED"))
    tracing_header: str = Field(default="X-Trace-ID", validation_alias=AliasChoices("TRACING_HEADER"))
    request_id_header: str = Field(default="X-Request-ID", validation_alias=AliasChoices("REQUEST_ID_HEADER"))
    metrics_enabled: bool = Field(default=True, validation_alias=AliasChoices("METRICS_ENABLED"))
    storage_bucket: str = Field(default="local", validation_alias=AliasChoices("STORAGE_BUCKET"))
    storage_base_path: Path = Field(default=Path("/var/getupsoft/storage"), validation_alias=AliasChoices("STORAGE_BASE_PATH"))
    odoo_rnc_catalog_path: Path = Field(
        default=Path("integration/odoo/odoo19_getupsoft_do_localization/local_rnc_directory.json"),
        validation_alias=AliasChoices("ODOO_RNC_CATALOG_PATH"),
    )
    llm_chat_enabled: bool = Field(default=True, validation_alias=AliasChoices("LLM_CHAT_ENABLED"))
    llm_provider: Literal["local", "openai_compatible"] = Field(
        default="local",
        validation_alias=AliasChoices("LLM_PROVIDER"),
    )
    llm_model: str = Field(default="tenant-rules-v1", validation_alias=AliasChoices("LLM_MODEL"))
    llm_api_base_url: str | None = Field(default=None, validation_alias=AliasChoices("LLM_API_BASE_URL"))
    llm_api_key: str | None = Field(default=None, validation_alias=AliasChoices("LLM_API_KEY"))
    llm_timeout_seconds: float = Field(default=20.0, gt=1.0, le=120.0, validation_alias=AliasChoices("LLM_TIMEOUT_SECONDS"))
    llm_max_context_invoices: int = Field(default=60, ge=5, le=200, validation_alias=AliasChoices("LLM_MAX_CONTEXT_INVOICES"))
    llm_max_completion_tokens: int = Field(default=500, ge=64, le=4000, validation_alias=AliasChoices("LLM_MAX_COMPLETION_TOKENS"))

    ui_tours_enabled: bool = Field(default=True, validation_alias=AliasChoices("UI_TOURS_ENABLED"))
    ui_tours_default_autorun: bool = Field(default=True, validation_alias=AliasChoices("UI_TOURS_DEFAULT_AUTORUN"))

    social_auth_enabled: bool = Field(default=False, validation_alias=AliasChoices("SOCIAL_AUTH_ENABLED"))
    social_auth_base_url: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_AUTH_BASE_URL"))
    social_auth_session_secret: str = Field(
        default="change-social-session",
        validation_alias=AliasChoices("SOCIAL_AUTH_SESSION_SECRET"),
    )

    social_google_enabled: bool = Field(default=False, validation_alias=AliasChoices("SOCIAL_GOOGLE_ENABLED"))
    social_google_client_id: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_GOOGLE_CLIENT_ID"))
    social_google_client_secret: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_GOOGLE_CLIENT_SECRET"))

    social_facebook_enabled: bool = Field(default=False, validation_alias=AliasChoices("SOCIAL_FACEBOOK_ENABLED"))
    social_facebook_client_id: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_FACEBOOK_CLIENT_ID"))
    social_facebook_client_secret: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_FACEBOOK_CLIENT_SECRET"))

    social_apple_enabled: bool = Field(default=False, validation_alias=AliasChoices("SOCIAL_APPLE_ENABLED"))
    social_apple_client_id: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_APPLE_CLIENT_ID"))
    social_apple_team_id: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_APPLE_TEAM_ID"))
    social_apple_key_id: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_APPLE_KEY_ID"))
    social_apple_private_key: str | None = Field(default=None, validation_alias=AliasChoices("SOCIAL_APPLE_PRIVATE_KEY"))
    social_apple_private_key_path: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("SOCIAL_APPLE_PRIVATE_KEY_PATH"),
    )

    smtp_host: str | None = Field(default=None, validation_alias=AliasChoices("SMTP_HOST"))
    smtp_port: int | None = Field(default=None, ge=1, le=65535, validation_alias=AliasChoices("SMTP_PORT"))
    smtp_user: str | None = Field(default=None, validation_alias=AliasChoices("SMTP_USER"))
    smtp_pass: str | None = Field(default=None, validation_alias=AliasChoices("SMTP_PASS"))
    smtp_secure: bool = Field(default=True, validation_alias=AliasChoices("SMTP_SECURE"))
    smtp_from: str | None = Field(default=None, validation_alias=AliasChoices("SMTP_FROM"))
    smtp_timeout_seconds: float = Field(default=20.0, gt=1.0, le=120.0, validation_alias=AliasChoices("SMTP_TIMEOUT_SECONDS"))

    bootstrap_admin_email: str = Field(
        default="admin@getupsoft.com.do",
        validation_alias=AliasChoices("BOOTSTRAP_ADMIN_EMAIL"),
    )
    bootstrap_admin_password: str = Field(
        default="ChangeMe123!",
        validation_alias=AliasChoices("BOOTSTRAP_ADMIN_PASSWORD"),
    )
    bootstrap_admin_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("BOOTSTRAP_ADMIN_ENABLED"),
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
    artifacts_root: Path = Field(default=Path("tests/artifacts"), validation_alias=AliasChoices("ARTIFACTS_ROOT"))
    sentry_dsn: str | None = Field(default=None)
    sentry_traces_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0, alias="SENTRY_TRACES")

    dgii_env: Literal["LOCAL", "TEST", "PRECERT", "CERT", "PROD"] = Field(default="TEST", validation_alias=AliasChoices("DGII_ENV", "ENV"))
    dgii_allowed_hosts_raw: str | None = Field(default=None, validation_alias=AliasChoices("DGII_ALLOWED_HOSTS"))
    dgii_rnc: str = Field(default="131415161", validation_alias=AliasChoices("DGII_RNC"))

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

    dgii_timeout: float = Field(default=5.0, gt=0, validation_alias=AliasChoices("DGII_TIMEOUT", "DGII_HTTP_TIMEOUT_SECONDS"))
    dgii_conn_timeout: float = Field(default=2.0, gt=0)
    dgii_max_retries: int = Field(default=3, ge=0, validation_alias=AliasChoices("DGII_MAX_RETRIES", "DGII_HTTP_RETRIES"))
    dgii_circuit_breaker_threshold: int = Field(default=5, ge=1)
    dgii_circuit_breaker_window: int = Field(default=60, ge=1)

    dgii_cert_p12_path: Path = Field(default=Path("/secrets/cert.p12"), validation_alias=AliasChoices("DGII_CERT_P12_PATH", "DGII_P12_PATH"))
    dgii_cert_p12_password: str = Field(default="changeit", validation_alias=AliasChoices("DGII_CERT_P12_PASSWORD", "DGII_P12_PASSWORD"))
    dgii_browser_automation_enabled: bool = Field(default=False, validation_alias=AliasChoices("DGII_BROWSER_AUTOMATION_ENABLED"))
    dgii_browser_automation_mode: Literal["assistive", "fallback", "evidence-only"] = Field(
        default="evidence-only",
        validation_alias=AliasChoices("DGII_BROWSER_AUTOMATION_MODE"),
    )
    odoo_sync_enabled: bool = Field(default=False, validation_alias=AliasChoices("ODOO_SYNC_ENABLED"))
    odoo_json2_base_url: str | None = Field(default=None, validation_alias=AliasChoices("ODOO_JSON2_BASE_URL"))
    odoo_json2_database: str | None = Field(default=None, validation_alias=AliasChoices("ODOO_JSON2_DATABASE"))
    odoo_json2_api_key: str | None = Field(default=None, validation_alias=AliasChoices("ODOO_JSON2_API_KEY"))
    odoo_timeout_seconds: float = Field(default=20.0, gt=1.0, le=120.0, validation_alias=AliasChoices("ODOO_TIMEOUT_SECONDS"))
    ri_qr_base_url: AnyUrl = Field(default="https://ri.mock/qr", validation_alias=AliasChoices("RI_QR_BASE_URL"))
    jobs_enabled: bool = Field(default=True, validation_alias=AliasChoices("JOBS_ENABLED"))
    recurring_invoice_job_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("RECURRING_INVOICE_JOB_ENABLED"),
    )
    recurring_invoice_poll_seconds: int = Field(
        default=60,
        ge=10,
        le=3600,
        validation_alias=AliasChoices("RECURRING_INVOICE_POLL_SECONDS"),
    )

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

    @staticmethod
    def _normalize_origin(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.startswith("http://") or stripped.startswith("https://"):
            return stripped
        return f"https://{stripped}"

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        env = str(self.environment).lower()
        smtp_configured = any(
            value not in {None, ""}
            for value in [self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_pass, self.smtp_from]
        )
        if smtp_configured:
            if not self.smtp_host or not self.smtp_port or not self.smtp_from:
                raise ValueError("SMTP_HOST, SMTP_PORT y SMTP_FROM son obligatorios cuando se configura SMTP")
            if bool(self.smtp_user) != bool(self.smtp_pass):
                raise ValueError("SMTP_USER y SMTP_PASS deben definirse juntos")

        social_providers_enabled = any(
            [self.social_google_enabled, self.social_facebook_enabled, self.social_apple_enabled]
        )
        if social_providers_enabled and not self.social_auth_enabled:
            raise ValueError("SOCIAL_AUTH_ENABLED debe ser true cuando se habilita algun proveedor social")

        if self.social_google_enabled and (
            not self.social_google_client_id or not self.social_google_client_secret
        ):
            raise ValueError("SOCIAL_GOOGLE_CLIENT_ID y SOCIAL_GOOGLE_CLIENT_SECRET son obligatorios")
        if self.social_facebook_enabled and (
            not self.social_facebook_client_id or not self.social_facebook_client_secret
        ):
            raise ValueError("SOCIAL_FACEBOOK_CLIENT_ID y SOCIAL_FACEBOOK_CLIENT_SECRET son obligatorios")
        if self.social_apple_enabled:
            apple_private_key_present = bool(self.social_apple_private_key or self.social_apple_private_key_path)
            if not (
                self.social_apple_client_id
                and self.social_apple_team_id
                and self.social_apple_key_id
                and apple_private_key_present
            ):
                raise ValueError(
                    "SOCIAL_APPLE_CLIENT_ID, SOCIAL_APPLE_TEAM_ID, SOCIAL_APPLE_KEY_ID y una private key son obligatorios"
                )

        if env in {"production", "prod"}:
            if self.jwt_secret in {"change-me", "dev-secret", ""}:
                raise ValueError("JWT_SECRET must be set to a non-default value in production")
            if self.social_auth_enabled and self.social_auth_session_secret in {
                "change-social-session",
                "dev-secret",
                "",
            }:
                raise ValueError("SOCIAL_AUTH_SESSION_SECRET debe definirse en produccion")
            if self.bootstrap_admin_enabled:
                default_passwords = {"ChangeMe123!", "change-me", "dev-secret", ""}
                if self.bootstrap_admin_password in default_passwords:
                    raise ValueError("BOOTSTRAP_ADMIN_PASSWORD must be set in production or disable bootstrap")
                if self.bootstrap_admin_email == "admin@getupsoft.com.do":
                    raise ValueError("BOOTSTRAP_ADMIN_EMAIL must be set in production or disable bootstrap")
        return self

    @computed_field
    @property
    def cors_allow_origins(self) -> List[str]:
        if self.cors_allow_origins_raw is None:
            origins = [
                "https://api.getupsoft.com.do",
                "https://app.getupsoft.com.do",
                "https://admin.getupsoft.com.do",
                "https://cliente.getupsoft.com.do",
                "https://socios.getupsoft.com.do",
                "https://www.getupsoft.com.do",
                "https://getupsoft.com.do",
                "http://api.getupsoft.com.do",
                "http://app.getupsoft.com.do",
                "http://admin.getupsoft.com.do",
                "http://cliente.getupsoft.com.do",
                "http://socios.getupsoft.com.do",
                "http://www.getupsoft.com.do",
                "http://getupsoft.com.do",
            ]
        else:
            origins = self._parse_csv_or_json_array(self.cors_allow_origins_raw)

        portal_origins = [
            self._normalize_origin(self.client_portal_domain),
            self._normalize_origin(self.app_portal_domain),
            self._normalize_origin(self.admin_portal_domain),
            self._normalize_origin(self.partner_portal_domain),
            self._normalize_origin(self.public_site_domain),
        ]
        for origin in portal_origins:
            if origin and origin not in origins:
                origins.append(origin)
        return origins

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
        if self.dgii_env in {"LOCAL", "TEST", "PRECERT"}:
            return str(self.dgii_auth_base_url_precert)
        if self.dgii_env == "CERT":
            return str(self.dgii_auth_base_url_cert)
        return str(self.dgii_auth_base_url_prod)

    @computed_field
    @property
    def dgii_recepcion_base_url(self) -> str:
        if self.dgii_env in {"LOCAL", "TEST", "PRECERT"}:
            return str(self.dgii_recepcion_base_url_precert)
        if self.dgii_env == "CERT":
            return str(self.dgii_recepcion_base_url_cert)
        return str(self.dgii_recepcion_base_url_prod)

    @computed_field
    @property
    def dgii_recepcion_fc_base_url(self) -> str:
        if self.dgii_env in {"LOCAL", "TEST", "PRECERT"}:
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
        if self.dgii_env in {"LOCAL", "TEST", "PRECERT"}:
            return str(self.dgii_consulta_resultado_base_url_precert)
        if self.dgii_env == "CERT":
            return str(self.dgii_consulta_resultado_base_url_cert)
        return str(self.dgii_consulta_resultado_base_url_prod)

    @computed_field
    @property
    def dgii_env_canonical(self) -> str:
        if self.dgii_env in {"LOCAL"}:
            return "LOCAL"
        if self.dgii_env in {"TEST", "PRECERT"}:
            return "TEST"
        return self.dgii_env

    @computed_field
    @property
    def dgii_p12_path(self) -> str:
        return str(self.dgii_cert_p12_path)

    @computed_field
    @property
    def dgii_p12_password(self) -> str:
        return self.dgii_cert_p12_password

    @computed_field
    @property
    def dgii_http_timeout_seconds(self) -> int:
        return int(self.dgii_timeout)

    @computed_field
    @property
    def dgii_http_retries(self) -> int:
        return int(self.dgii_max_retries)

    def resolve_service_urls(self) -> dict[str, str]:
        """Return the base URLs for the active DGII environment."""

        return {
            "auth": self.dgii_auth_base_url,
            "recepcion": self.dgii_recepcion_base_url,
            "recepcion_fc": self.dgii_recepcion_fc_base_url,
            "directorio": self.dgii_consulta_directorio_base_url,
        }

    def url_for(self, service: str) -> str:
        """Return the base URL for the given DGII service."""

        mapping = self.resolve_service_urls()
        try:
            return mapping[service]
        except KeyError as exc:  # pragma: no cover
            raise KeyError(f"Servicio DGII desconocido: {service}") from exc

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

    @computed_field
    @property
    def social_callback_base_url(self) -> str:
        base = (self.social_auth_base_url or "").strip()
        if base:
            return base.rstrip("/")
        return "https://api.getupsoft.com.do"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
