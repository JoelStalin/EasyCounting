import { useCallback, useMemo } from "react";
import { useAuthStore } from "../store/auth-store";

export function useAuth() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const refreshToken = useAuthStore((state) => state.refreshToken);
  const user = useAuthStore((state) => state.user);
  const permissions = useAuthStore((state) => state.permissions);
  const hydrated = useAuthStore((state) => state.hydrated);
  const clearSession = useAuthStore((state) => state.clearSession);
  const setSession = useAuthStore((state) => state.setSession);

  const hasPermission = useCallback((permission: string) => {
    return permissions.includes(permission);
  }, [permissions]);

  const hasAnyPermission = useCallback(
    (required: string[]) => {
      if (required.length === 0) {
        return true;
      }
      return required.some((permission) => permissions.includes(permission));
    },
    [permissions]
  );

  const scope = useMemo(() => user?.scope ?? null, [user]);
  const tenantId = useMemo(() => user?.tenantId ?? null, [user]);

  return {
    accessToken,
    refreshToken,
    user,
    permissions,
    scope,
    tenantId,
    isAuthenticated: Boolean(accessToken && user),
    loading: !hydrated,
    logout: clearSession,
    setSession,
    hasPermission,
    hasAnyPermission,
  };
}
