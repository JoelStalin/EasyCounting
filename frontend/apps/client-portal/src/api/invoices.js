import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
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
export function useEmitInvoice() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/cliente/invoices/emit", payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "invoices"] });
        },
    });
}
export function useSendInvoiceEmail() {
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post(`/api/v1/cliente/invoices/${payload.invoiceId}/send-email`, { recipient: payload.recipient });
            return data;
        },
    });
}
