import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";
export function useMyToursQuery(enabled) {
    return useQuery({
        queryKey: ["ui-tours", "me", "client"],
        enabled,
        queryFn: async () => {
            const { data } = await api.get("/api/v1/ui-tours/me");
            return data;
        },
    });
}
export function useUpsertTourMutation() {
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.put(`/api/v1/ui-tours/${payload.viewKey}`, {
                tourVersion: payload.tourVersion,
                status: payload.status,
                lastStep: payload.lastStep,
            });
            return data;
        },
    });
}
