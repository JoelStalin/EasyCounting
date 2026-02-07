import { type ChangeEvent, type PropsWithChildren, FormEvent, useEffect, useState } from "react";
import { NavLink, Outlet, useParams } from "react-router-dom";
import { useAccountingSummary, useCreateLedgerEntry, useLedgerEntries, useTenantSettings, useUpdateTenantSettings } from "../api/accounting";
import { useAdminInvoices } from "../api/dashboard";
import { useAssignTenantPlan, useTenant, useTenantPlan, useUpdateTenant } from "../api/tenants";
import { type Plan, usePlans } from "../api/plans";

const TABS = [
  { to: "overview", label: "Resumen" },
  { to: "invoices", label: "Comprobantes" },
  { to: "accounting", label: "Contabilidad" },
  { to: "plans", label: "Planes" },
  { to: "certificates", label: "Certificados" },
  { to: "users", label: "Usuarios" },
  { to: "settings", label: "Parámetros" },
];

export function CompanyDetailLayout() {
  const { id } = useParams();
  const tenantQuery = useTenant(id);
  const tenant = tenantQuery.data;

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">
          {tenantQuery.isLoading ? "Cargando compañía…" : tenant ? `Compañía: ${tenant.name}` : `Detalle de compañía #${id}`}
        </h1>
        <p className="text-sm text-slate-300">Consulta comprobantes, planes tarifarios y equipos delegados.</p>
      </header>
      {tenantQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el detalle de la compañía.
        </div>
      ) : null}
      <nav className="flex flex-wrap gap-3">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }: { isActive: boolean }) =>
              `rounded-full border px-4 py-1 text-sm transition ${isActive ? "border-primary bg-primary/20 text-primary" : "border-slate-700 text-slate-300 hover:border-primary hover:text-primary"}`
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <Outlet />
      </div>
    </div>
  );
}

export function CompanyOverviewTab() {
  const { id } = useParams();
  const tenantQuery = useTenant(id);
  const tenant = tenantQuery.data;

  return (
    <div className="space-y-4 text-sm text-slate-300">
      <p>
        RNC emisor: <span className="font-mono text-slate-100">{tenantQuery.isLoading ? "…" : tenant?.rnc ?? "—"}</span>
      </p>
      <p>
        Ambiente actual: <span className="font-semibold text-primary">{tenantQuery.isLoading ? "…" : tenant?.env ?? "—"}</span>
      </p>
      <p>Última sincronización DGII: hace 12 minutos.</p>
    </div>
  );
}

export function CompanyInvoicesTab() {
  const { id } = useParams();
  const tenantId = id ? Number(id) : undefined;
  const [estado, setEstado] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [page, setPage] = useState(1);

  const invoicesQuery = useAdminInvoices({
    tenantId,
    page,
    size: 20,
    estado: estado || undefined,
    dateFrom: dateFrom ? `${dateFrom}T00:00:00` : undefined,
    dateTo: dateTo ? `${dateTo}T00:00:00` : undefined,
  });
  const invoices = invoicesQuery.data;
  const invoiceItems = invoices?.items ?? [];

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-4">
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-slate-400">Estado DGII</label>
          <select
            value={estado}
            onChange={(event: ChangeEvent<HTMLSelectElement>) => {
              setEstado(event.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          >
            <option value="">Todos</option>
            <option value="ACEPTADO">ACEPTADO</option>
            <option value="RECHAZADO">RECHAZADO</option>
            <option value="pendiente">pendiente</option>
          </select>
        </div>
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-slate-400">Desde</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(event: ChangeEvent<HTMLInputElement>) => {
              setDateFrom(event.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs uppercase tracking-wide text-slate-400">Hasta</label>
          <input
            type="date"
            value={dateTo}
            onChange={(event: ChangeEvent<HTMLInputElement>) => {
              setDateTo(event.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </div>
        <div className="flex items-end justify-end">
          <button
            type="button"
            onClick={() => {
              setEstado("");
              setDateFrom("");
              setDateTo("");
              setPage(1);
            }}
            className="rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary"
          >
            Limpiar filtros
          </button>
        </div>
      </div>

      {invoicesQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el listado de comprobantes.
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="min-w-full divide-y divide-slate-800 text-sm text-slate-300">
          <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-3 py-2 text-left">Fecha</th>
              <th className="px-3 py-2 text-left">ENCF</th>
              <th className="px-3 py-2 text-left">Tipo</th>
              <th className="px-3 py-2 text-left">TrackID</th>
              <th className="px-3 py-2 text-left">Estado DGII</th>
              <th className="px-3 py-2 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            {invoiceItems.map((item) => (
              <tr key={item.id} className="border-b border-slate-800/80 hover:bg-slate-900/40">
                <td className="px-3 py-2">{new Date(item.fecha_emision).toLocaleString()}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{item.encf}</td>
                <td className="px-3 py-2">{item.tipo_ecf}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{item.track_id ?? "—"}</td>
                <td className="px-3 py-2">{item.estado_dgii}</td>
                <td className="px-3 py-2 text-right">
                  {Number(item.total).toLocaleString("es-DO", {
                    style: "currency",
                    currency: "DOP",
                  })}
                </td>
              </tr>
            ))}

            {invoicesQuery.isLoading ? (
              <tr>
                <td className="px-3 py-6 text-center text-sm text-slate-500" colSpan={6}>
                  Cargando comprobantes…
                </td>
              </tr>
            ) : null}

            {invoiceItems.length === 0 && !invoicesQuery.isLoading ? (
              <tr>
                <td className="px-3 py-6 text-center text-sm text-slate-500" colSpan={6}>
                  No hay comprobantes para los filtros actuales.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-400">
        <span>
          Página {invoices?.page ?? page} · Total {invoices?.total ?? 0}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="rounded-md border border-slate-700 px-3 py-1.5 font-semibold text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Anterior
          </button>
          <button
            type="button"
            onClick={() => setPage((p) => p + 1)}
            disabled={invoiceItems.length < 20}
            className="rounded-md border border-slate-700 px-3 py-1.5 font-semibold text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Siguiente
          </button>
        </div>
      </div>
    </div>
  );
}

export function CompanyAccountingTab() {
  const { id } = useParams();
  const summaryQuery = useAccountingSummary(id);
  const ledgerQuery = useLedgerEntries(id);
  const createLedgerEntry = useCreateLedgerEntry(id);
  const [form, setForm] = useState({
    invoice_id: "",
    referencia: "",
    cuenta: "",
    descripcion: "",
    debit: "0.00",
    credit: "0.00",
    fecha: new Date().toISOString().slice(0, 16),
  });

  const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    createLedgerEntry.mutate({
      invoice_id: form.invoice_id ? Number(form.invoice_id) : null,
      referencia: form.referencia,
      cuenta: form.cuenta,
      descripcion: form.descripcion || null,
      debit: form.debit || "0",
      credit: form.credit || "0",
      fecha: new Date(form.fecha).toISOString(),
    });
  };

  const summary = summaryQuery.data;
  const ledger = ledgerQuery.data;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total emitidos" value={summary?.totales.total_emitidos ?? 0} />
        <StatCard label="Aceptados" value={summary?.totales.total_aceptados ?? 0} />
        <StatCard label="Pendientes contables" value={summary?.contabilidad.pendientes ?? 0} />
        <StatCard
          label="Monto emitido"
          value={summary ? Number(summary.totales.total_monto).toLocaleString("es-DO", { style: "currency", currency: "DOP" }) : "RD$0.00"}
          isCurrency
        />
      </section>

      <section className="space-y-3">
        <h3 className="text-lg font-semibold text-white">Registrar asiento</h3>
        <form onSubmit={handleSubmit} className="grid gap-3 rounded-xl border border-slate-800 bg-slate-900/40 p-4 md:grid-cols-2">
          <input
            name="invoice_id"
            value={form.invoice_id}
            onChange={handleChange}
            placeholder="ID del comprobante (opcional)"
            className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
          <input
            required
            name="referencia"
            value={form.referencia}
            onChange={handleChange}
            placeholder="Referencia contable"
            className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
          <input
            required
            name="cuenta"
            value={form.cuenta}
            onChange={handleChange}
            placeholder="Cuenta contable"
            className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
          <input
            required
            type="datetime-local"
            name="fecha"
            value={form.fecha}
            onChange={handleChange}
            className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
          <input
            name="debit"
            value={form.debit}
            onChange={handleChange}
            placeholder="Débito"
            className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
          <input
            name="credit"
            value={form.credit}
            onChange={handleChange}
            placeholder="Crédito"
            className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
          <textarea
            name="descripcion"
            value={form.descripcion}
            onChange={handleChange}
            placeholder="Descripción"
            className="col-span-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
            rows={2}
          />
          <div className="col-span-full flex justify-end">
            <button
              type="submit"
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700"
              disabled={createLedgerEntry.isPending}
            >
              {createLedgerEntry.isPending ? "Guardando…" : "Registrar asiento"}
            </button>
          </div>
        </form>
      </section>

      <section className="space-y-3">
        <header className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Libro contable</h3>
          <p className="text-xs text-slate-400">Mostrando {ledger?.items.length ?? 0} de {ledger?.total ?? 0} asientos</p>
        </header>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm text-slate-300">
            <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-3 py-2 text-left">Fecha</th>
                <th className="px-3 py-2 text-left">Referencia</th>
                <th className="px-3 py-2 text-left">ENCF</th>
                <th className="px-3 py-2 text-left">Cuenta</th>
                <th className="px-3 py-2 text-right">Débito</th>
                <th className="px-3 py-2 text-right">Crédito</th>
              </tr>
            </thead>
            <tbody>
              {ledger?.items.map((item) => (
                <tr key={item.id} className="border-b border-slate-800/80 hover:bg-slate-900/40">
                  <td className="px-3 py-2">{new Date(item.fecha).toLocaleString()}</td>
                  <td className="px-3 py-2 font-medium text-slate-100">{item.referencia}</td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-400">{item.encf ?? "—"}</td>
                  <td className="px-3 py-2">{item.cuenta}</td>
                  <td className="px-3 py-2 text-right text-emerald-300">{Number(item.debit).toLocaleString("es-DO", { minimumFractionDigits: 2 })}</td>
                  <td className="px-3 py-2 text-right text-rose-300">{Number(item.credit).toLocaleString("es-DO", { minimumFractionDigits: 2 })}</td>
                </tr>
              ))}
              {ledger?.items.length === 0 && (
                <tr>
                  <td className="px-3 py-6 text-center text-sm text-slate-500" colSpan={6}>
                    Aún no se registran asientos contables para esta empresa.
                  </td>
                </tr>
              )}
              {!ledger && (
                <tr>
                  <td className="px-3 py-6 text-center text-sm text-slate-500" colSpan={6}>
                    Cargando libro contable…
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export function CompanyPlansTab() {
  const { id } = useParams();
  const plansQuery = usePlans();
  const tenantPlanQuery = useTenantPlan(id);
  const assignPlan = useAssignTenantPlan(id);
  const [selectedPlanId, setSelectedPlanId] = useState<string>("");

  useEffect(() => {
    const current = tenantPlanQuery.data?.plan?.id;
    setSelectedPlanId(current ? String(current) : "");
  }, [tenantPlanQuery.data?.plan?.id]);

  const currentPlanName = tenantPlanQuery.data?.plan?.name ?? "Sin plan asignado";

  return (
    <div className="space-y-4 text-sm text-slate-300">
      <p>
        Plan vigente: <span className="font-semibold text-primary">{tenantPlanQuery.isLoading ? "Cargando…" : currentPlanName}</span>
      </p>

      {plansQuery.isError || tenantPlanQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar la información de planes.
        </div>
      ) : null}

      <div className="grid gap-3 rounded-xl border border-slate-800 bg-slate-900/40 p-4 md:grid-cols-3">
        <label className="space-y-1 text-sm text-slate-200 md:col-span-2">
          Asignar plan
          <select
            value={selectedPlanId}
            onChange={(e: ChangeEvent<HTMLSelectElement>) => setSelectedPlanId(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
            disabled={plansQuery.isLoading || tenantPlanQuery.isLoading}
          >
            <option value="">Sin plan</option>
            {(plansQuery.data ?? []).map((plan: Plan) => (
              <option key={plan.id} value={String(plan.id)}>
                {plan.name}
              </option>
            ))}
          </select>
        </label>

        <div className="flex items-end justify-end">
          <button
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700"
            disabled={assignPlan.isPending}
            onClick={() => assignPlan.mutate(selectedPlanId ? Number(selectedPlanId) : null)}
            type="button"
          >
            {assignPlan.isPending ? "Guardando…" : "Guardar"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function CompanyCertificatesTab() {
  return (
    <div className="space-y-4 text-sm text-slate-300">
      <p>Último certificado subido: 2024-05-01.</p>
      <button className="rounded-md border border-dashed border-primary px-4 py-2 text-sm text-primary hover:bg-primary/10">
        Subir .p12
      </button>
    </div>
  );
}

export function CompanyUsersTab() {
  return (
    <div className="space-y-4 text-sm text-slate-300">
      <p>Usuarios delegados (RBAC multi-tenant) se mostrarán aquí.</p>
      <button className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
        Invitar usuario
      </button>
    </div>
  );
}

export function CompanySettingsTab() {
  const { id } = useParams();
  const tenantQuery = useTenant(id);
  const updateTenant = useUpdateTenant(id);
  const settingsQuery = useTenantSettings(id);
  const updateSettings = useUpdateTenantSettings(id);
  const [issuerForm, setIssuerForm] = useState({
    name: "",
    rnc: "",
  });
  const [settingsForm, setSettingsForm] = useState({
    moneda: "DOP",
    cuenta_ingresos: "",
    cuenta_itbis: "",
    cuenta_retenciones: "",
    dias_credito: 0,
    correo_facturacion: "",
    telefono_contacto: "",
    notas: "",
  });

  useEffect(() => {
    if (tenantQuery.data) {
      setIssuerForm({
        name: tenantQuery.data.name,
        rnc: tenantQuery.data.rnc,
      });
    }
  }, [tenantQuery.data]);

  useEffect(() => {
    if (settingsQuery.data) {
      setSettingsForm({
        moneda: settingsQuery.data.moneda,
        cuenta_ingresos: settingsQuery.data.cuenta_ingresos ?? "",
        cuenta_itbis: settingsQuery.data.cuenta_itbis ?? "",
        cuenta_retenciones: settingsQuery.data.cuenta_retenciones ?? "",
        dias_credito: settingsQuery.data.dias_credito,
        correo_facturacion: settingsQuery.data.correo_facturacion ?? "",
        telefono_contacto: settingsQuery.data.telefono_contacto ?? "",
        notas: settingsQuery.data.notas ?? "",
      });
    }
  }, [settingsQuery.data]);

  const handleIssuerChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setIssuerForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSettingsChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setSettingsForm((prev) => ({ ...prev, [name]: name === "dias_credito" ? Number(value) : value }));
  };

  const handleIssuerSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateTenant.mutate({
      name: issuerForm.name,
      rnc: issuerForm.rnc,
    });
  };

  const handleSettingsSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateSettings.mutate({
      moneda: settingsForm.moneda,
      cuenta_ingresos: settingsForm.cuenta_ingresos || null,
      cuenta_itbis: settingsForm.cuenta_itbis || null,
      cuenta_retenciones: settingsForm.cuenta_retenciones || null,
      dias_credito: settingsForm.dias_credito,
      correo_facturacion: settingsForm.correo_facturacion || null,
      telefono_contacto: settingsForm.telefono_contacto || null,
      notas: settingsForm.notas || null,
    });
  };

  return (
    <div className="space-y-8">
      <form onSubmit={handleIssuerSubmit} className="grid gap-4 md:grid-cols-2">
        <Field label="Nombre / razon social del emisor">
          <input
            name="name"
            value={issuerForm.name}
            onChange={handleIssuerChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <Field label="RNC del emisor">
          <input
            name="rnc"
            value={issuerForm.rnc}
            onChange={handleIssuerChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <div className="md:col-span-2 flex justify-end gap-3">
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700"
            disabled={updateTenant.isPending}
          >
            {updateTenant.isPending ? "Guardando..." : "Guardar emisor"}
          </button>
        </div>
      </form>

      <form onSubmit={handleSettingsSubmit} className="grid gap-4 md:grid-cols-2">
        <Field label="Moneda">
          <input
            name="moneda"
            value={settingsForm.moneda}
            onChange={handleSettingsChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <Field label="Dias de credito">
          <input
            name="dias_credito"
            type="number"
            min={0}
            max={365}
            value={settingsForm.dias_credito}
            onChange={handleSettingsChange}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <Field label="Cuenta de ingresos">
          <input
            name="cuenta_ingresos"
            value={settingsForm.cuenta_ingresos}
            onChange={handleSettingsChange}
            placeholder="701-VENT"
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <Field label="Cuenta de ITBIS">
          <input
            name="cuenta_itbis"
            value={settingsForm.cuenta_itbis}
            onChange={handleSettingsChange}
            placeholder="208-ITBIS"
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <Field label="Cuenta de retenciones">
          <input
            name="cuenta_retenciones"
            value={settingsForm.cuenta_retenciones}
            onChange={handleSettingsChange}
            placeholder="209-RET"
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <Field label="Correo para facturacion">
          <input
            name="correo_facturacion"
            value={settingsForm.correo_facturacion}
            onChange={handleSettingsChange}
            type="email"
            placeholder="facturacion@empresa.do"
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <Field label="Telefono de contacto">
          <input
            name="telefono_contacto"
            value={settingsForm.telefono_contacto}
            onChange={handleSettingsChange}
            placeholder="809-555-0000"
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <Field label="Notas internas" className="md:col-span-2">
          <textarea
            name="notas"
            value={settingsForm.notas}
            onChange={handleSettingsChange}
            rows={3}
            className="w-full rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
          />
        </Field>
        <div className="md:col-span-2 flex justify-end gap-3">
          {settingsQuery.data?.updated_at && (
            <span className="self-center text-xs text-slate-500">Ultima actualizacion: {new Date(settingsQuery.data.updated_at).toLocaleString()}</span>
          )}
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700"
            disabled={updateSettings.isPending}
          >
            {updateSettings.isPending ? "Guardando..." : "Guardar cambios"}
          </button>
        </div>
      </form>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  isCurrency?: boolean;
}

function StatCard({ label, value, isCurrency }: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${isCurrency ? "text-primary" : "text-slate-100"}`}>{value}</p>
    </div>
  );
}

interface FieldProps extends PropsWithChildren {
  label: string;
  className?: string;
}

function Field({ label, children, className }: FieldProps) {
  return (
    <label className={`flex flex-col gap-1 text-sm text-slate-200 ${className ?? ""}`}>
      <span className="text-xs uppercase tracking-wide text-slate-400">{label}</span>
      {children}
    </label>
  );
}
