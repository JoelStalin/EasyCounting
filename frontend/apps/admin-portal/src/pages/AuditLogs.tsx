import { JsonView } from "../components/JsonView";
import { useAuditLogs } from "../api/audit";

export function AuditLogsPage() {
  const logsQuery = useAuditLogs(50);

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Auditoría</h1>
        <p className="text-sm text-slate-300">
          Registros WORM con hash encadenado para cumplimiento DGII y PCI DSS.
        </p>
      </header>
      {logsQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudieron cargar los logs de auditoría.
        </div>
      ) : null}
      <JsonView data={logsQuery.isLoading ? { loading: true } : logsQuery.data ?? []} />
    </div>
  );
}
