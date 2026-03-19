import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";
import { useAuth } from "../auth/use-auth";
import type { AuthSession } from "../store/auth-store";

interface LoginPayload {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
    scope: "PLATFORM" | "TENANT" | "PARTNER";
    tenant_id: string | null;
    roles: string[];
  };
  permissions: string[];
  mfa_required: boolean;
}

export function useLoginMutation() {
  const { setSession } = useAuth();
  return useMutation({
    mutationFn: async (payload: LoginPayload) => {
      const { data } = await api.post<LoginResponse>("/api/v1/auth/login", payload);
      return data;
    },
    onSuccess: (data: LoginResponse) => {
      if (!data.mfa_required) {
        const session: AuthSession = {
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          user: {
            id: data.user.id,
            email: data.user.email,
            scope: data.user.scope,
            tenantId: data.user.tenant_id,
            roles: data.user.roles,
          },
          permissions: data.permissions,
        };
        setSession(session);
      }
    },
  });
}

export function useProfileQuery(enabled: boolean) {
  const { setSession } = useAuth();
  return useQuery({
    queryKey: ["me"],
    enabled,
    queryFn: async () => {
      const { data } = await api.get<LoginResponse>("/api/v1/me");
      const session: AuthSession = {
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        user: {
          id: data.user.id,
          email: data.user.email,
          scope: data.user.scope,
          tenantId: data.user.tenant_id,
          roles: data.user.roles,
        },
        permissions: data.permissions,
      };
      setSession(session);
      return data;
    },
  });
}
