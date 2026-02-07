import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function useTenants() {
    return useQuery({
        queryKey: ["admin", "tenants"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/admin/tenants");
            return data;
        },
    });
}
export function useTenant(tenantId) {
    return useQuery({
        queryKey: ["admin", "tenant", tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const { data } = await api.get(`/api/v1/admin/tenants/${tenantId}`);
            return data;
        },
    });
}
export function useCreateTenant() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/admin/tenants", payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "tenants"] });
        },
    });
}
export function useUpdateTenant(tenantId) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.put(`/api/v1/admin/tenants/${tenantId}`, payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "tenant", tenantId] });
            await queryClient.invalidateQueries({ queryKey: ["admin", "tenants"] });
        },
    });
}
export function useTenantPlan(tenantId) {
    return useQuery({
        queryKey: ["admin", "tenant-plan", tenantId],
        enabled: Boolean(tenantId),
        queryFn: async () => {
            const { data } = await api.get(`/api/v1/admin/tenants/${tenantId}/plan`);
            return data;
        },
    });
}
export function useAssignTenantPlan(tenantId) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (planId) => {
            const { data } = await api.put(`/api/v1/admin/tenants/${tenantId}/plan`, {
                plan_id: planId,
            });
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "tenant-plan", tenantId] });
        },
    });
}
