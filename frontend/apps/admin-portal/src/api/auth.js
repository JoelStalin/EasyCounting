import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";
import { useAuth } from "../auth/use-auth";
export function useLoginMutation() {
    const { setSession } = useAuth();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/auth/login", payload);
            return data;
        },
        onSuccess: (data) => {
            if (!data.mfa_required) {
                const session = {
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
export function useProfileQuery(enabled) {
    const { setSession } = useAuth();
    return useQuery({
        queryKey: ["me"],
        enabled,
        queryFn: async () => {
            const { data } = await api.get("/me");
            const session = {
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
