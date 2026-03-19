import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function useTenantApiTokens() {
    return useQuery({
        queryKey: ["tenant", "api-tokens"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/api-tokens");
            return data;
        },
    });
}
export function useCreateTenantApiToken() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/cliente/api-tokens", payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "api-tokens"] });
        },
    });
}
export function useRevokeTenantApiToken() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (tokenId) => {
            const { data } = await api.delete(`/api/v1/cliente/api-tokens/${tokenId}`);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "api-tokens"] });
        },
    });
}
