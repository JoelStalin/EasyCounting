import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function usePlans() {
    return useQuery({
        queryKey: ["tenant", "plans"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/plans");
            return data;
        },
    });
}
export function useTenantPlan() {
    return useQuery({
        queryKey: ["tenant", "plan"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/plan");
            return data;
        },
    });
}
export function useRequestPlanChange() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (planId) => {
            const { data } = await api.put("/api/v1/cliente/plan", {
                plan_id: planId,
            });
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "plan"] });
            await queryClient.invalidateQueries({ queryKey: ["tenant", "usage"] });
        },
    });
}
