import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
export function useInvoices(params) {
    return useQuery({
        queryKey: ["tenant", "invoices", params],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/invoices", {
                params: {
                    page: params?.page,
                    size: params?.size,
                    estado_dgii: params?.estado,
                    encf: params?.encf,
                },
            });
            return data;
        },
    });
}
export function useInvoiceDetail(invoiceId) {
    return useQuery({
        queryKey: ["tenant", "invoice", invoiceId],
        enabled: Boolean(invoiceId),
        queryFn: async () => {
            const { data } = await api.get(`/api/v1/cliente/invoices/${invoiceId}`);
            return data;
        },
    });
}
