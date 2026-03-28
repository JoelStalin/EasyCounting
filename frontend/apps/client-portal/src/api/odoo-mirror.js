import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";
export function useSyncOdoo() {
    return useMutation({
        mutationFn: async (payload = {}) => {
            const body = {
                includeCustomers: payload.includeCustomers ?? true,
                includeVendors: payload.includeVendors ?? true,
                includeProducts: payload.includeProducts ?? true,
                includeInvoices: payload.includeInvoices ?? true,
                limit: payload.limit ?? 100,
            };
            const { data } = await api.post("/api/v1/cliente/integrations/odoo/sync", body);
            return data;
        },
    });
}
export function useOdooCustomers(limit = 20) {
    return useQuery({
        queryKey: ["odoo-customers", limit],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/integrations/odoo/customers", { params: { limit } });
            return data;
        },
    });
}
export function useOdooVendors(limit = 20) {
    return useQuery({
        queryKey: ["odoo-vendors", limit],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/integrations/odoo/vendors", { params: { limit } });
            return data;
        },
    });
}
export function useOdooProducts(limit = 20) {
    return useQuery({
        queryKey: ["odoo-products", limit],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/integrations/odoo/products", { params: { limit } });
            return data;
        },
    });
}
export function useOdooInvoices(limit = 20) {
    return useQuery({
        queryKey: ["odoo-invoices", limit],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/integrations/odoo/invoices", { params: { limit } });
            return data;
        },
    });
}
