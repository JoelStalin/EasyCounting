import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
export function useUsageSummary(params) {
    return useQuery({
        queryKey: ["tenant", "usage", params],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/usage", {
                params: {
                    month: params?.month,
                    page: params?.page,
                    size: params?.size,
                },
            });
            return data;
        },
    });
}
