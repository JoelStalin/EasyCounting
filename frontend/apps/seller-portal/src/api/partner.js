import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function usePartnerProfile(enabled = true) {
    return useQuery({
        queryKey: ["partner", "me"],
        enabled,
        queryFn: async () => {
            const { data } = await api.get("/api/v1/partner/me");
            return data;
        },
    });
}
export function usePartnerDashboard() {
    return useQuery({
        queryKey: ["partner", "dashboard"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/partner/dashboard");
            return data;
        },
    });
}
export function usePartnerTenants() {
    return useQuery({
        queryKey: ["partner", "tenants"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/partner/tenants");
            return data;
        },
    });
}
export function usePartnerInvoices(params = {}) {
    const page = params.page ?? 1;
    const size = params.size ?? 20;
    return useQuery({
        queryKey: ["partner", "invoices", params.tenantId ?? null, page, size],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/partner/invoices", {
                params: {
                    page,
                    size,
                    tenant_id: params.tenantId ?? undefined,
                },
            });
            return data;
        },
    });
}
export function useEmitPartnerInvoice() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/partner/emit", payload);
            return data;
        },
        onSuccess: async () => {
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ["partner", "dashboard"] }),
                queryClient.invalidateQueries({ queryKey: ["partner", "tenants"] }),
                queryClient.invalidateQueries({ queryKey: ["partner", "invoices"] }),
            ]);
        },
    });
}
