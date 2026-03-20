"""Permission catalog and role-to-permission mapping."""
from __future__ import annotations

from collections.abc import Iterable

from app.security.enums import (
    GlobalRole,
    LEGACY_ROLE_TO_GLOBAL_ROLE,
    LEGACY_ROLE_TO_TENANT_ROLE,
    Permission,
    TenantRole,
)

GLOBAL_ROLE_PERMISSIONS: dict[GlobalRole, set[Permission]] = {
    GlobalRole.ROOT: {
        Permission.PORTAL_BOOTSTRAP_VIEW,
        Permission.PLATFORM_TENANT_VIEW,
        Permission.PLATFORM_PLAN_CRUD,
        Permission.PLATFORM_AUDIT_VIEW,
        Permission.PLATFORM_USER_MANAGE,
        Permission.PLATFORM_AI_PROVIDER_MANAGE,
        Permission.PLATFORM_MATRIX_ISSUER_MANAGE,
        Permission.PLATFORM_ROLE_REQUEST_REVIEW,
    },
    GlobalRole.ADMIN: {
        Permission.PORTAL_BOOTSTRAP_VIEW,
        Permission.PLATFORM_TENANT_VIEW,
        Permission.PLATFORM_PLAN_CRUD,
        Permission.PLATFORM_AUDIT_VIEW,
        Permission.PLATFORM_USER_MANAGE,
        Permission.PLATFORM_ROLE_REQUEST_REVIEW,
    },
    GlobalRole.USER: {
        Permission.PORTAL_BOOTSTRAP_VIEW,
        Permission.ROLE_CHANGE_REQUEST_CREATE,
    },
}

TENANT_ROLE_PERMISSIONS: dict[TenantRole, set[Permission]] = {
    TenantRole.PARTNER_OWNER: {
        Permission.PARTNER_DASHBOARD_VIEW,
        Permission.PARTNER_TENANT_VIEW,
        Permission.PARTNER_CLIENT_VIEW,
        Permission.PARTNER_CLIENT_MANAGE,
        Permission.PARTNER_USER_MANAGE,
        Permission.PARTNER_INVOICE_READ,
        Permission.PARTNER_INVOICE_EMIT,
        Permission.PARTNER_COMMISSION_VIEW,
    },
    TenantRole.PARTNER_OPERATOR: {
        Permission.PARTNER_DASHBOARD_VIEW,
        Permission.PARTNER_TENANT_VIEW,
        Permission.PARTNER_CLIENT_VIEW,
        Permission.PARTNER_CLIENT_MANAGE,
        Permission.PARTNER_INVOICE_READ,
        Permission.PARTNER_INVOICE_EMIT,
        Permission.PARTNER_COMMISSION_VIEW,
    },
    TenantRole.PARTNER_AUDITOR: {
        Permission.PARTNER_DASHBOARD_VIEW,
        Permission.PARTNER_TENANT_VIEW,
        Permission.PARTNER_CLIENT_VIEW,
        Permission.PARTNER_INVOICE_READ,
        Permission.PARTNER_COMMISSION_VIEW,
    },
    TenantRole.TENANT_ADMIN: {
        Permission.TENANT_INVOICE_READ,
        Permission.TENANT_INVOICE_EMIT,
        Permission.TENANT_RECURRING_INVOICE_MANAGE,
        Permission.TENANT_RFCE_SUBMIT,
        Permission.TENANT_APPROVAL_SEND,
        Permission.TENANT_CERT_UPLOAD,
        Permission.TENANT_CHAT_ASSIST,
        Permission.TENANT_API_TOKEN_MANAGE,
        Permission.TENANT_PLAN_VIEW,
        Permission.TENANT_PLAN_UPGRADE,
        Permission.TENANT_USAGE_VIEW,
        Permission.TENANT_PROFILE_MANAGE,
        Permission.TENANT_FISCAL_PROFILE_MANAGE,
        Permission.TENANT_SETTINGS_MANAGE,
        Permission.TENANT_SECURITY_MANAGE,
        Permission.TENANT_RI_VIEW,
    },
    TenantRole.TENANT_OPERATOR: {
        Permission.TENANT_INVOICE_READ,
        Permission.TENANT_INVOICE_EMIT,
        Permission.TENANT_RECURRING_INVOICE_MANAGE,
        Permission.TENANT_RFCE_SUBMIT,
        Permission.TENANT_APPROVAL_SEND,
        Permission.TENANT_CHAT_ASSIST,
        Permission.TENANT_API_TOKEN_MANAGE,
        Permission.TENANT_PLAN_VIEW,
        Permission.TENANT_USAGE_VIEW,
        Permission.TENANT_PROFILE_MANAGE,
        Permission.TENANT_FISCAL_PROFILE_MANAGE,
        Permission.TENANT_RI_VIEW,
    },
    TenantRole.TENANT_VIEWER: {
        Permission.TENANT_INVOICE_READ,
        Permission.TENANT_USAGE_VIEW,
        Permission.TENANT_PLAN_VIEW,
        Permission.TENANT_RI_VIEW,
    },
}


def permissions_for_assignment(
    *,
    global_role: GlobalRole,
    tenant_role: TenantRole | None = None,
    legacy_role: str | None = None,
) -> set[Permission]:
    permissions = set(GLOBAL_ROLE_PERMISSIONS.get(global_role, set()))
    if tenant_role is not None:
        permissions.update(TENANT_ROLE_PERMISSIONS.get(tenant_role, set()))
    elif legacy_role:
        mapped_role = LEGACY_ROLE_TO_TENANT_ROLE.get(legacy_role)
        if mapped_role is not None:
            permissions.update(TENANT_ROLE_PERMISSIONS.get(mapped_role, set()))
    return permissions


def derive_global_role(global_role: str | None, legacy_role: str | None) -> GlobalRole:
    if global_role:
        try:
            return GlobalRole(global_role.upper())
        except ValueError:
            pass
    if legacy_role and legacy_role in LEGACY_ROLE_TO_GLOBAL_ROLE:
        return LEGACY_ROLE_TO_GLOBAL_ROLE[legacy_role]
    return GlobalRole.USER


def derive_tenant_role(tenant_role: str | None, legacy_role: str | None) -> TenantRole | None:
    if tenant_role:
        try:
            return TenantRole(tenant_role.upper())
        except ValueError:
            pass
    if legacy_role:
        return LEGACY_ROLE_TO_TENANT_ROLE.get(legacy_role)
    return None


def scope_name(*, global_role: GlobalRole, tenant_role: TenantRole | None, legacy_role: str | None) -> str:
    if global_role in {GlobalRole.ROOT, GlobalRole.ADMIN} or (legacy_role or "").startswith("platform_"):
        return "PLATFORM"
    if tenant_role in {TenantRole.PARTNER_OWNER, TenantRole.PARTNER_OPERATOR, TenantRole.PARTNER_AUDITOR} or (
        legacy_role or ""
    ).startswith("partner_"):
        return "PARTNER"
    return "TENANT"


def permission_names(items: Iterable[Permission]) -> list[str]:
    return sorted(item.value for item in items)
