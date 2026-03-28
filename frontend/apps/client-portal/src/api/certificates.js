import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
export function useTenantCertificates() {
    return useQuery({
        queryKey: ["tenant", "certificates"],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/cliente/certificates");
            return data;
        },
    });
}
export function useUploadTenantCertificate() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload) => {
            const formData = new FormData();
            formData.append("alias", payload.alias);
            formData.append("password", payload.password);
            formData.append("activate", payload.activate === false ? "false" : "true");
            formData.append("certificate", payload.certificate);
            const { data } = await api.post("/api/v1/cliente/certificates", formData);
            return data;
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({ queryKey: ["tenant", "certificates"] });
        },
    });
}
