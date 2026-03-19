import { useMutation } from "@tanstack/react-query";
import { api } from "./client";
export function useTenantChat() {
    return useMutation({
        mutationFn: async (payload) => {
            const { data } = await api.post("/api/v1/cliente/chat/ask", payload);
            return data;
        },
    });
}
