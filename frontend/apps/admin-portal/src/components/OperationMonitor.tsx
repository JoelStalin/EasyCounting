import { useEffect, useMemo, useState } from "react";
import { useOperation, useOperations, useOperationStream } from "../api/operations";
import type { OperationEventItem } from "../api/operations";

interface OperationMonitorProps {
  tenantId?: string;
}

// ---------------------------------------------------------------------------
// SSE connection status badge
// ---------------------------------------------------------------------------
function ConnectionBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    connected: { label: "SSE en vivo", cls: "bg-emerald-900/40 text-emerald-400 border-emerald-700" },
    connecting: { label: "Conectando…", cls: "bg-yellow-900/40 text-yellow-400 border-yellow-700" },
    error: { label: "Polling", cls: "bg-orange-900/40 text-orange-400 border-orange-700" },
    closed: { label: "Inactivo", cls: "bg-slate-800 text-slate-400 border-slate-700" },
  };
  const { label, cls } = map[status] ?? map.closed;
  return (
    <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${cls}`}>
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function OperationMonitor({ tenantId }: OperationMonitorProps) {
  const operationsQuery = useOperations(tenantId);
  const operations = operationsQuery.data?.items ?? [];
  const [selectedOperationId, setSelectedOperationId] = useState<string>("");

  // Auto-select first operation
  useEffect(() => {
    if (!selectedOperationId && operations.length > 0) {
      setSelectedOperationId(operations[0].operation_id);
    }
  }, [operations, selectedOperationId]);

  // Polling fallback for operation detail
  const operationQuery = useOperation(selectedOperationId);
  const operation = operationQuery.data;

  // SSE real-time stream for events
  const { events: sseEvents, connection } = useOperationStream(selectedOperationId || undefined);

  // Merge SSE events with polled events (SSE takes priority for new events)
  const mergedEvents = useMemo<OperationEventItem[]>(() => {
    const polled = operation?.events ?? [];
    if (sseEvents.length === 0) return polled;

    // Build a map from polled events, then overlay SSE events
    const byId = new Map<number, OperationEventItem>();
    for (const ev of polled) byId.set(ev.id, ev);
    for (const ev of sseEvents) byId.set(ev.id, ev);

    return Array.from(byId.values()).sort((a, b) => a.id - b.id);
  }, [operation?.events, sseEvents]);

  return (
    <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
      <header className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Monitor técnico DGII / Odoo</h3>
          <p className="text-xs text-slate-400">
            Eventos en tiempo real vía SSE con fallback a polling controlado.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ConnectionBadge status={connection.status} />
          <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
            {operations.length} operaciones
          </span>
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-[300px,1fr]">
        {/* ---------------------------------------------------------------- */}
        {/* Operation list (left panel)                                       */}
        {/* ---------------------------------------------------------------- */}
        <div className="space-y-2">
          {operations.map((item) => (
            <button
              key={item.operation_id}
              type="button"
              onClick={() => setSelectedOperationId(item.operation_id)}
              className={`w-full rounded-xl border p-3 text-left transition ${
                selectedOperationId === item.operation_id
                  ? "border-primary bg-primary/10"
                  : "border-slate-800 bg-slate-900/40 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-slate-300">
                  {item.document_number ?? item.operation_id.slice(0, 12)}
                </span>
                <span className="text-[10px] uppercase tracking-wide text-primary">{item.state}</span>
              </div>
              <p className="mt-1 text-sm text-slate-100">
                {item.document_type} · {item.environment}
              </p>
              <p className="mt-1 text-xs text-slate-400">
                TrackId: {item.dgii_track_id ?? "pendiente"}
              </p>
            </button>
          ))}
          {operations.length === 0 && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-center text-xs text-slate-500">
              Sin operaciones registradas.
            </div>
          )}
        </div>

        {/* ---------------------------------------------------------------- */}
        {/* Operation detail (right panel)                                    */}
        {/* ---------------------------------------------------------------- */}
        <div className="space-y-4">
          {!operation ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 text-center text-sm text-slate-500">
              Selecciona una operación para ver el detalle.
            </div>
          ) : (
            <>
              {/* Metrics */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Metric label="Estado" value={operation.state} />
                <Metric label="Ambiente" value={operation.environment} />
                <Metric label="TrackId DGII" value={operation.dgii_track_id ?? "—"} mono />
                <Metric label="Odoo Sync" value={operation.odoo_sync_state} />
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                <Meta label="Tipo" value={operation.document_type} />
                <Meta label="Número" value={operation.document_number ?? "—"} mono />
                <Meta label="Monto" value={`${operation.currency} ${operation.amount_total}`} mono />
                <Meta label="Reintentos" value={String(operation.retry_count)} />
                <Meta label="Iniciado" value={new Date(operation.started_at).toLocaleString()} />
                {operation.completed_at && (
                  <Meta label="Completado" value={new Date(operation.completed_at).toLocaleString()} />
                )}
              </div>

              {/* SSE connection info */}
              {connection.status === "error" && connection.error && (
                <div className="rounded-lg border border-orange-800 bg-orange-950/30 px-3 py-2 text-xs text-orange-300">
                  ⚠️ {connection.error}
                </div>
              )}

              {/* Events timeline */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-slate-100">
                    Eventos ({mergedEvents.length})
                  </h4>
                  {sseEvents.length > 0 && (
                    <span className="text-[10px] text-emerald-400">
                      +{sseEvents.length} en vivo
                    </span>
                  )}
                </div>
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {mergedEvents.map((event) => (
                    <EventRow key={event.id} event={event} />
                  ))}
                  {mergedEvents.length === 0 && (
                    <p className="text-xs text-slate-500">Sin eventos registrados aún.</p>
                  )}
                </div>
              </div>

              {/* Evidence */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <h4 className="mb-3 text-sm font-semibold text-slate-100">Evidencia</h4>
                <div className="space-y-2">
                  {operation.evidence.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-300"
                    >
                      <span>{item.artifact_type}</span>
                      <span className="font-mono text-slate-400 truncate max-w-[200px]">
                        {item.file_path}
                      </span>
                    </div>
                  ))}
                  {operation.evidence.length === 0 && (
                    <p className="text-xs text-slate-500">Aún no hay archivos asociados.</p>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function EventRow({ event }: { event: OperationEventItem }) {
  const stateColors: Record<string, string> = {
    ACCEPTED: "text-emerald-400",
    ACCEPTED_CONDITIONAL: "text-teal-400",
    REJECTED: "text-red-400",
    FAILED_TECHNICAL: "text-red-500",
    CANCELLED: "text-slate-500",
    QUEUED: "text-slate-400",
    SENDING_TO_DGII: "text-blue-400",
    DGII_RESPONSE_RECEIVED: "text-blue-300",
    TRACKID_REGISTERED: "text-cyan-400",
    SYNCING_TO_ODOO: "text-violet-400",
    SYNCED_TO_ODOO: "text-violet-300",
    RETRYING: "text-yellow-400",
  };
  const colorCls = stateColors[event.status] ?? "text-primary";

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-slate-100">{event.title}</span>
        <span className={`text-[10px] uppercase tracking-wide font-semibold ${colorCls}`}>
          {event.status}
        </span>
      </div>
      <p className="mt-1 text-[10px] text-slate-500">
        {new Date(event.occurred_at).toLocaleString()}
        {event.duration_ms != null && ` · ${event.duration_ms}ms`}
        {event.stage && ` · ${event.stage}`}
      </p>
      {event.message && <p className="mt-2 text-sm text-slate-300">{event.message}</p>}
    </div>
  );
}

function Metric({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-2 text-sm ${mono ? "font-mono text-slate-200" : "font-semibold text-white"}`}>
        {value}
      </p>
    </div>
  );
}

function Meta({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-sm ${mono ? "font-mono text-slate-300" : "text-slate-200"}`}>
        {value}
      </p>
    </div>
  );
}
