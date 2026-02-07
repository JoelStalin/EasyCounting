import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function useTenantSettings(tenantId) {
    return useQuery({
        queryKey: ["admin", "tenant-settings", tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const { data } = await api.get(`/api/v1/admin/tenants/${tenantId}/settings`);
            return data;
        },
    });
}
export function useUpdateTenantSettings(tenantId) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.put(`/api/v1/admin/tenants/${tenantId}/settings`, payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "tenant-settings", tenantId] });
        },
    });
}
export function useAccountingSummary(tenantId) {
    return useQuery({
        queryKey: ["admin", "accounting-summary", tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const { data } = await api.get(`/api/v1/admin/tenants/${tenantId}/accounting/summary`);
            return data;
        },
    });
}
export function useLedgerEntries(tenantId, page = 1, size = 20) {
    return useQuery({
        queryKey: ["admin", "ledger-entries", tenantId, page, size],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const { data } = await api.get(`/api/v1/admin/tenants/${tenantId}/accounting/ledger`, {
                params: { page, size },
            });
            return data;
        },
    });
}
export function useCreateLedgerEntry(tenantId) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post(`/api/v1/admin/tenants/${tenantId}/accounting/ledger`, payload);
            return data;
        },
        onSuccess: async () => {
            await Promise.all([
                queryClient.invalidateQueries({ queryKey: ["admin", "ledger-entries", tenantId] }),
                queryClient.invalidateQueries({ queryKey: ["admin", "accounting-summary", tenantId] }),
            ]);
        },
    });
}
