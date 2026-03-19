import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";
export function useOnboardingQuery(enabled) {
    return useQuery({
        queryKey: ["tenant-onboarding"],
        enabled,
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/onboarding");
            return data;
        },
    });
}
export function useCompleteOnboardingMutation() {
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.put("/api/v1/cliente/onboarding", payload);
            return data;
        },
    });
}
