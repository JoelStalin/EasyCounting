import { useEffect, useState } from "react";
import { useOperation, useOperations } from "../api/operations";

interface OperationMonitorProps {
  tenantId?: string;
}

export function OperationMonitor({ tenantId }: OperationMonitorProps) {
  const operationsQuery = useOperations(tenantId);
  const operations = operationsQuery.data?.items ?? [];
  const [selectedOperationId, setSelectedOperationId] = useState<string>("");

  useEffect(() => {
    if (!selectedOperationId && operations.length > 0) {
      setSelectedOperationId(operations[0].operation_id);
    }
  }, [operations, selectedOperationId]);

  const operationQuery = useOperation(selectedOperationId);
  const operation = operationQuery.data;

  return (
    <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
      <header className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Monitor tecnico DGII / Odoo</h3>
          <p className="text-xs text-slate-400">Actualizacion viva por polling controlado y eventos persistidos.</p>
        </div>
        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
          {operations.length} operaciones
        </span>
      </header>

      <div className="grid gap-4 lg:grid-cols-[300px,1fr]">
        <div className="space-y-2">
          {operations.map((item) => (
            <button
              key={item.operation_id}
              type="button"
              onClick={() => setSelectedOperationId(item.operation_id)}
              className={`w-full rounded-xl border p-3 text-left transition ${
                selectedOperationId === item.operation_id ? "border-primary bg-primary/10" : "border-slate-800 bg-slate-900/40 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-xs text-slate-300">{item.document_number ?? item.operation_id.slice(0, 12)}</span>
                <span className="text-[10px] uppercase tracking-wide text-primary">{item.state}</span>
              </div>
              <p className="mt-1 text-sm text-slate-100">{item.document_type} · {item.environment}</p>
              <p className="mt-1 text-xs text-slate-400">TrackId: {item.dgii_track_id ?? "pendiente"}</p>
            </button>
          ))}
          {operations.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-700 p-4 text-sm text-slate-500">
              No hay operaciones recientes para este tenant.
            </div>
          ) : null}
        </div>

        <div className="space-y-4">
          {!operation ? (
            <div className="rounded-xl border border-dashed border-slate-700 p-6 text-sm text-slate-500">
              Selecciona una operacion para ver sus eventos.
            </div>
          ) : (
            <>
              <div className="grid gap-3 md:grid-cols-3">
                <Metric label="Estado" value={operation.state} />
                <Metric label="TrackId" value={operation.dgii_track_id ?? "pendiente"} mono />
                <Metric label="Sync Odoo" value={operation.odoo_sync_state} />
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <div className="grid gap-2 md:grid-cols-2">
                  <Meta label="operationId" value={operation.operation_id} mono />
                  <Meta label="correlationId" value={operation.correlation_id} mono />
                  <Meta label="Monto" value={`${Number(operation.amount_total).toFixed(6)} ${operation.currency}`} />
                  <Meta label="Ultimo cambio" value={new Date(operation.last_transition_at).toLocaleString()} />
                </div>
                {operation.last_error_message ? (
                  <div className="mt-3 rounded-lg border border-rose-900/40 bg-rose-950/20 p-3 text-sm text-rose-200">
                    {operation.last_error_message}
                  </div>
                ) : null}
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <h4 className="mb-3 text-sm font-semibold text-slate-100">Linea de eventos</h4>
                <div className="space-y-3">
                  {operation.events.map((event) => (
                    <div key={event.id} className="rounded-lg border border-slate-800 bg-slate-950/60 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-medium text-slate-100">{event.title}</span>
                        <span className="text-[10px] uppercase tracking-wide text-primary">{event.status}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-400">{new Date(event.occurred_at).toLocaleString()}</p>
                      {event.message ? <p className="mt-2 text-sm text-slate-300">{event.message}</p> : null}
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                <h4 className="mb-3 text-sm font-semibold text-slate-100">Evidencia</h4>
                <div className="space-y-2">
                  {operation.evidence.map((item) => (
                    <div key={item.id} className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs text-slate-300">
                      <span>{item.artifact_type}</span>
                      <span className="font-mono text-slate-400">{item.file_path}</span>
                    </div>
                  ))}
                  {operation.evidence.length === 0 ? <p className="text-xs text-slate-500">Aun no hay archivos asociados.</p> : null}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-2 text-sm ${mono ? "font-mono text-slate-200" : "font-semibold text-white"}`}>{value}</p>
    </div>
  );
}

function Meta({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-sm ${mono ? "font-mono text-slate-300" : "text-slate-200"}`}>{value}</p>
    </div>
  );
}
