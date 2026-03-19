import { useMutation, useQuery } from "@tanstack/react-query";
import { api, resolveApiBaseUrl } from "./client";
import { useAuth } from "../auth/use-auth";
import type { AuthSession } from "../store/auth-store";

interface LoginPayload {
  email: string;
  password: string;
  portal: "admin";
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
    scope: "PLATFORM" | "TENANT";
    tenant_id: string | null;
    roles: string[];
    onboarding_status?: string | null;
  };
  permissions: string[];
  mfa_required: boolean;
  challenge_id?: string | null;
}

export interface SocialProviderItem {
  provider: "google" | "facebook" | "apple";
  label: string;
}

export interface SocialExchangePendingMFA {
  mfaRequired: true;
  challengeId: string;
  permissions: string[];
  returnTo?: string | null;
  user: AuthSession["user"];
}

export type SocialExchangeResponse = (AuthSession & { returnTo?: string | null }) | SocialExchangePendingMFA;

function toSession(data: LoginResponse): AuthSession {
  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    user: {
      id: data.user.id,
      email: data.user.email,
      scope: data.user.scope,
      tenantId: data.user.tenant_id,
      roles: data.user.roles,
      onboardingStatus: data.user.onboarding_status ?? null,
    },
    permissions: data.permissions,
  };
}

export function useLoginMutation() {
  const { setSession } = useAuth();
  return useMutation({
    mutationFn: async (payload: Omit<LoginPayload, "portal">) => {
      const { data } = await api.post<LoginResponse>("/api/v1/auth/login", { ...payload, portal: "admin" });
      return data;
    },
    onSuccess: (data) => {
      if (!data.mfa_required) {
        setSession(toSession(data));
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
      const session = toSession(data);
      setSession(session);
      return data;
    },
  });
}

export function useSocialProvidersQuery() {
  return useQuery({
    queryKey: ["social-providers", "admin"],
    queryFn: async () => {
      const { data } = await api.get<SocialProviderItem[]>("/api/v1/auth/oauth/providers", {
        params: { portal: "admin" },
      });
      return data;
    },
  });
}

export function startSocialLogin(provider: SocialProviderItem["provider"], returnTo: string) {
  const url = new URL(`/api/v1/auth/oauth/${provider}/start`, resolveApiBaseUrl());
  url.searchParams.set("portal", "admin");
  url.searchParams.set("return_to", returnTo);
  window.location.assign(url.toString());
}

export async function exchangeSocialTicket(ticket: string): Promise<SocialExchangeResponse> {
  const { data } = await api.post<SocialExchangeResponse>("/api/v1/auth/oauth/exchange", {
    ticket,
    portal: "admin",
  });
  return data;
}
