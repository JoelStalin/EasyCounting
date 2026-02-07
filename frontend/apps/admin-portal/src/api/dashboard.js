import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
export function useDashboardKpis(month) {
    return useQuery({
        queryKey: ["admin", "dashboard", "kpis", month],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/admin/dashboard/kpis", {
                params: month ? { month } : undefined,
            });
            return data;
        },
    });
}
export function useAdminInvoices(params) {
    return useQuery({
        queryKey: ["admin", "invoices", params],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/admin/invoices", {
                params: {
                    page: params?.page ?? 1,
                    size: params?.size ?? 20,
                    tenant_id: params?.tenantId,
                    estado_dgii: params?.estado,
                    tipo_ecf: params?.tipoEcf,
                    encf: params?.encf,
                    track_id: params?.trackId,
                    date_from: params?.dateFrom,
                    date_to: params?.dateTo,
                },
            });
            return data;
        },
    });
}
