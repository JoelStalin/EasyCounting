import { useState } from "react";
import { Link } from "react-router-dom";
import { DataTable } from "../components/DataTable";
import { FileDownloader } from "../components/FileDownloader";
import { type TenantItem, useCreateTenant, useTenants } from "../api/tenants";

interface CompanyRow {
  id: string;
  name: string;
  rnc: string;
  env: string;
  status: string;
}

export function CompaniesPage() {
  const tenantsQuery = useTenants();
  const createTenant = useCreateTenant();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", rnc: "", env: "testecf" });

  const handleCreate = async () => {
    await createTenant.mutateAsync({
      name: form.name,
      rnc: form.rnc,
      env: form.env,
      dgii_base_ecf: null,
      dgii_base_fc: null,
    });
    setOpen(false);
    setForm({ name: "", rnc: "", env: "testecf" });
  };

  const rows: CompanyRow[] = (tenantsQuery.data ?? []).map((tenant: TenantItem) => ({
    id: String(tenant.id),
    name: tenant.name,
    rnc: tenant.rnc,
    env: tenant.env,
    status: tenant.status,
  }));

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Compañías</h1>
          <p className="text-sm text-slate-300">Gestiona tenants, ambientes DGII y certificados.</p>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
        >
          Crear compañía
        </button>
      </header>

      {tenantsQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el listado de compañías.
        </div>
      ) : null}

      <DataTable
        data={rows}
        columns={[
          {
            header: "Compañía",
            cell: (row) => (
              <div className="space-y-1">
                <Link className="text-sm font-semibold text-primary" to={`/companies/${row.id}`}>
                  {row.name}
                </Link>
                <p className="text-xs text-slate-400">RNC: {row.rnc}</p>
              </div>
            ),
          },
          { header: "Ambiente", cell: (row) => <span className="text-sm text-slate-200">{row.env}</span> },
          { header: "Estado", cell: (row) => <span className="text-sm text-slate-200">{row.status}</span> },
          {
            header: "Documentos",
            cell: () => (
              <div className="flex gap-2">
                <FileDownloader href="#" label="XML" />
                <FileDownloader href="#" label="RI" />
              </div>
            ),
          },
        ]}
        emptyMessage={
          tenantsQuery.isLoading
            ? "Cargando compañías…"
            : tenantsQuery.isError
              ? "Error cargando compañías"
              : "Sin compañías registradas"
        }
      />

      {open ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-lg space-y-4 rounded-xl border border-slate-800 bg-slate-950 p-6">
            <header className="space-y-1">
              <h2 className="text-lg font-semibold text-white">Crear compañía</h2>
              <p className="text-sm text-slate-400">Registra un nuevo tenant y define el ambiente DGII.</p>
            </header>
            <div className="grid gap-3">
              <label className="space-y-1 text-sm text-slate-300">
                Nombre
                <input
                  value={form.name}
                  onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                />
              </label>
              <label className="space-y-1 text-sm text-slate-300">
                RNC
                <input
                  value={form.rnc}
                  onChange={(e) => setForm((prev) => ({ ...prev, rnc: e.target.value }))}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                />
              </label>
              <label className="space-y-1 text-sm text-slate-300">
                Ambiente
                <select
                  value={form.env}
                  onChange={(e) => setForm((prev) => ({ ...prev, env: e.target.value }))}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                >
                  <option value="testecf">PRECERT (testecf)</option>
                  <option value="certecf">CERT (certecf)</option>
                  <option value="ecf">PROD (ecf)</option>
                </select>
              </label>
            </div>

            {createTenant.isError ? (
              <div className="rounded-lg border border-rose-900/60 bg-rose-950/30 p-3 text-sm text-rose-200">
                No se pudo crear la compañía. Verifica RNC y vuelve a intentar.
              </div>
            ) : null}

            <footer className="flex justify-end gap-2">
              <button
                onClick={() => setOpen(false)}
                className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-200"
                type="button"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreate}
                disabled={createTenant.isPending || !form.name || !form.rnc}
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:bg-slate-700"
                type="button"
              >
                {createTenant.isPending ? "Creando…" : "Crear"}
              </button>
            </footer>
          </div>
        </div>
      ) : null}
    </div>
  );
}
