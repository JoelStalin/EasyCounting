import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface OperationListItem {
  operation_id: string;
  correlation_id: string;
  request_id?: string | null;
  tenant_id: number;
  invoice_id?: number | null;
  document_type: string;
  document_number?: string | null;
  environment: string;
  source_system: string;
  state: string;
  dgii_track_id?: string | null;
  odoo_sync_state: string;
  amount_total: string;
  currency: string;
  retry_count: number;
  initiated_by?: string | null;
  last_error_code?: string | null;
  last_error_message?: string | null;
  started_at: string;
  completed_at?: string | null;
  last_transition_at: string;
}

export interface OperationEventItem {
  id: number;
  status: string;
  title: string;
  message?: string | null;
  stage?: string | null;
  duration_ms?: number | null;
  details_json: Record<string, unknown>;
  occurred_at: string;
}

export interface OperationDetail extends OperationListItem {
  metadata_json: Record<string, unknown>;
  events: OperationEventItem[];
  evidence: Array<{
    id: number;
    artifact_type: string;
    file_path: string;
    content_type?: string | null;
    checksum?: string | null;
    size_bytes?: number | null;
    metadata_json: Record<string, unknown>;
  }>;
}

export interface OperationListResponse {
  items: OperationListItem[];
  total: number;
}

export function useOperations(tenantId?: string) {
  return useQuery({
    queryKey: ["admin", "operations", tenantId],
    enabled: Boolean(tenantId),
    refetchInterval: 2500,
    queryFn: async () => {
      const { data } = await api.get<OperationListResponse>("/api/v1/operations", {
        params: { tenant_id: tenantId, limit: 20 },
      });
      return data;
    },
  });
}

export function useOperation(operationId?: string) {
  return useQuery({
    queryKey: ["admin", "operation", operationId],
    enabled: Boolean(operationId),
    refetchInterval: 1500,
    queryFn: async () => {
      const { data } = await api.get<OperationDetail>(`/api/v1/operations/${operationId}`);
      return data;
    },
  });
}
