import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function useAIProviders() {
    return useQuery({
        queryKey: ["admin", "ai-providers"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/admin/ai-providers");
            return data;
        },
    });
}
export function useCreateAIProvider() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/admin/ai-providers", payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
        },
    });
}
export function useUpdateAIProvider(providerId) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.put(`/api/v1/admin/ai-providers/${providerId}`, payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
        },
    });
}
export function useDeleteAIProvider() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (providerId) => {
            await api.delete(`/api/v1/admin/ai-providers/${providerId}`);
            return providerId;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
        },
    });
}
