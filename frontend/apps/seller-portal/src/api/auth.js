import { useMutation, useQuery } from "@tanstack/react-query";
import { api, resolveApiBaseUrl } from "./client";
import { useAuth } from "../auth/use-auth";
function toSession(data) {
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
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/auth/login", { ...payload, portal: "seller" });
            return data;
        },
        onSuccess: (data) => {
            if (!data.mfa_required) {
                setSession(toSession(data));
            }
        },
    });
}
export function useProfileQuery(enabled) {
    const { setSession } = useAuth();
    return useQuery({
        queryKey: ["me"],
        enabled,
        queryFn: async () => {
            const { data } = await api.get("/api/v1/me");
            const session = toSession(data);
            setSession(session);
            return data;
        },
    });
}
export function useSocialProvidersQuery() {
    return useQuery({
        queryKey: ["social-providers", "seller"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/auth/oauth/providers", {
                params: { portal: "seller" },
            });
            return data;
        },
    });
}
export function startSocialLogin(provider, returnTo) {
    const url = new URL(`/api/v1/auth/oauth/${provider}/start`, resolveApiBaseUrl());
    url.searchParams.set("portal", "seller");
    url.searchParams.set("return_to", returnTo);
    window.location.assign(url.toString());
}
export async function exchangeSocialTicket(ticket) {
    const { data } = await api.post("/api/v1/auth/oauth/exchange", {
        ticket,
        portal: "seller",
    });
    return data;
}
