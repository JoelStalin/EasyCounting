import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface AuditLogItem {
  id: number;
  tenant_id: number;
  actor: string;
  action: string;
  resource: string;
  hash_prev: string;
  hash_curr: string;
  created_at: string;
}

export function useAuditLogs(limit = 50, tenantId?: number) {
  return useQuery({
    queryKey: ["admin", "audit-logs", limit, tenantId],
    queryFn: async () => {
      const { data } = await api.get<AuditLogItem[]>("/api/v1/admin/audit-logs", {
        params: { limit, tenant_id: tenantId },
      });
      return data;
    },
  });
}
