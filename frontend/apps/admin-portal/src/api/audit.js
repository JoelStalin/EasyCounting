import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
export function useAuditLogs(limit = 50, tenantId) {
    return useQuery({
        queryKey: ["admin", "audit-logs", limit, tenantId],
        queryFn: async () => {
            const { data } = await api.get("/api/v1/admin/audit-logs", {
                params: { limit, tenant_id: tenantId },
            });
            return data;
        },
    });
}
