import { Link } from "react-router-dom";
import { usePlans } from "../api/plans";
import { DataTable } from "../components/DataTable";

interface PlanRow {
  id: number;
  name: string;
  documentos_incluidos: number;
  precio_mensual: string;
  precio_por_documento: string;
}

export function PlansPage() {
  const plansQuery = usePlans();
  const rows: PlanRow[] = (plansQuery.data ?? []).map((plan) => ({
    id: plan.id,
    name: plan.name,
    documentos_incluidos: plan.documentos_incluidos,
    precio_mensual: plan.precio_mensual,
    precio_por_documento: plan.precio_por_documento,
  }));

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Planes tarifarios</h1>
          <p className="text-sm text-slate-300">Define reglas de monetización para los tenants de GetUpNet.</p>
        </div>
        <Link className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90" to="/plans/new">
          Nuevo plan
        </Link>
      </header>
      {plansQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el listado de planes.
        </div>
      ) : null}
      <DataTable
        data={rows}
        columns={[
          { header: "Nombre", cell: (row) => <span className="font-semibold text-slate-200">{row.name}</span> },
          { header: "Incluidos", cell: (row) => <span className="text-sm text-slate-300">{row.documentos_incluidos}</span> },
          { header: "Mensual", cell: (row) => <span className="text-sm text-slate-300">{row.precio_mensual}</span> },
          { header: "Por doc.", cell: (row) => <span className="text-sm text-slate-300">{row.precio_por_documento}</span> },
        ]}
        emptyMessage={plansQuery.isLoading ? "Cargando planes…" : plansQuery.isError ? "Error cargando planes" : "Sin planes"}
      />
    </div>
  );
}
