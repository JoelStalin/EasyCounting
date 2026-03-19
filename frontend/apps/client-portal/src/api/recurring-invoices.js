import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function useRecurringInvoices() {
    return useQuery({
        queryKey: ["tenant", "recurring-invoices"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/recurring-invoices");
            return data;
        },
    });
}
export function useCreateRecurringInvoice() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/cliente/recurring-invoices", payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "recurring-invoices"] });
            await queryClient.invalidateQueries({ queryKey: ["tenant", "invoices"] });
        },
    });
}
export function usePauseRecurringInvoice() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (scheduleId) => {
            const { data } = await api.post(`/api/v1/cliente/recurring-invoices/${scheduleId}/pause`);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "recurring-invoices"] });
        },
    });
}
export function useResumeRecurringInvoice() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (scheduleId) => {
            const { data } = await api.post(`/api/v1/cliente/recurring-invoices/${scheduleId}/resume`);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "recurring-invoices"] });
        },
    });
}
export function useRunDueRecurringInvoices() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async () => {
            const { data } = await api.post("/api/v1/cliente/recurring-invoices/run-due");
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "recurring-invoices"] });
            await queryClient.invalidateQueries({ queryKey: ["tenant", "invoices"] });
            await queryClient.invalidateQueries({ queryKey: ["tenant", "usage"] });
        },
    });
}
