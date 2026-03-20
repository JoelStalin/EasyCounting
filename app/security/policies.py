"""Policy objects for auth context resolution."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.security.enums import GlobalRole, Permission, TenantRole


@dataclass(slots=True)
class AuthContext:
    """Resolved authentication and authorization context."""

    subject: str
    token_payload: dict[str, Any]
    user: Any | None = None
    membership: Any | None = None
    session: Any | None = None
    global_role: GlobalRole = GlobalRole.USER
    tenant_role: TenantRole | None = None
    legacy_role: str | None = None
    active_tenant_id: int | None = None
    permission_set: set[Permission] = field(default_factory=set)
    scopes: list[str] = field(default_factory=list)

    @property
    def user_id(self) -> int | None:
        try:
            return int(self.subject)
        except (TypeError, ValueError):
            return getattr(self.user, "id", None)

    @property
    def permission_names(self) -> list[str]:
        return sorted(item.value for item in self.permission_set)

    @property
    def scope(self) -> str:
        if self.global_role in {GlobalRole.ROOT, GlobalRole.ADMIN} or (self.legacy_role or "").startswith("platform_"):
            return "PLATFORM"
        if self.tenant_role in {TenantRole.PARTNER_OWNER, TenantRole.PARTNER_OPERATOR, TenantRole.PARTNER_AUDITOR} or (
            self.legacy_role or ""
        ).startswith("partner_"):
            return "PARTNER"
        return "TENANT"

    def has_permission(self, permission: Permission | str) -> bool:
        target = permission if isinstance(permission, Permission) else Permission(permission)
        return target in self.permission_set

    def require_user(self) -> Any:
        if self.user is None:
            raise ValueError("This operation requires a persisted user context")
        return self.user
