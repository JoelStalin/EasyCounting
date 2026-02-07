import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function usePlans() {
    return useQuery({
        queryKey: ["admin", "plans"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/admin/plans");
            return data;
        },
    });
}
export function useCreatePlan() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/admin/plans", payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
        },
    });
}
export function useUpdatePlan(planId) {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.put(`/api/v1/admin/plans/${planId}`, payload);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
        },
    });
}
export function useDeletePlan() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (planId) => {
            await api.delete(`/api/v1/admin/plans/${planId}`);
            return planId;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
        },
    });
}
