import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
export function usePlatformUsers() {
    return useQuery({
        queryKey: ["admin", "platform-users"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/admin/users");
            return data;
        },
    });
}
