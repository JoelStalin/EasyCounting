import { useEffect, useRef, useState } from "react";
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

// ---------------------------------------------------------------------------
// SSE hook — real-time operation events via EventSource
// ---------------------------------------------------------------------------

export interface SSEConnectionState {
  status: "connecting" | "connected" | "error" | "closed";
  lastEventId: number;
  error?: string;
}

/**
 * useOperationStream — connects to the SSE stream for a given operation.
 * Falls back gracefully if EventSource is not supported.
 * New events are appended to the `events` array in real-time.
 */
export function useOperationStream(operationId?: string) {
  const [events, setEvents] = useState<OperationEventItem[]>([]);
  const [connection, setConnection] = useState<SSEConnectionState>({
    status: "closed",
    lastEventId: 0,
  });
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!operationId) return;

    // Reset on operation change
    setEvents([]);
    setConnection({ status: "connecting", lastEventId: 0 });

    if (typeof EventSource === "undefined") {
      setConnection({ status: "error", lastEventId: 0, error: "EventSource not supported" });
      return;
    }

    const baseUrl = (api.defaults.baseURL ?? "").replace(/\/$/, "");
    const url = `${baseUrl}/api/v1/operations/${operationId}/stream`;

    const es = new EventSource(url, { withCredentials: true });
    esRef.current = es;

    es.addEventListener("open", () => {
      setConnection((prev) => ({ ...prev, status: "connected" }));
    });

    es.addEventListener("operation_event", (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as OperationEventItem;
        setEvents((prev) => {
          // Deduplicate by id
          if (prev.some((ev) => ev.id === data.id)) return prev;
          return [...prev, data];
        });
        setConnection((prev) => ({
          ...prev,
          status: "connected",
          lastEventId: Math.max(prev.lastEventId, data.id),
        }));
      } catch {
        // ignore parse errors
      }
    });

    es.addEventListener("error", () => {
      setConnection((prev) => ({
        ...prev,
        status: "error",
        error: "SSE connection error — falling back to polling",
      }));
      es.close();
    });

    return () => {
      es.close();
      esRef.current = null;
      setConnection({ status: "closed", lastEventId: 0 });
    };
  }, [operationId]);

  const closeStream = () => {
    esRef.current?.close();
    esRef.current = null;
    setConnection({ status: "closed", lastEventId: 0 });
  };

  return { events, connection, closeStream };
}

// ---------------------------------------------------------------------------
// Polling hooks (kept as fallback / primary for list view)
// ---------------------------------------------------------------------------

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
