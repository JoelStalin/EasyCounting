import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { RequirePermission } from "../auth/guards";
import { useTenantPlan } from "../api/plans";
import {
  RecurringFrequency,
  useCreateRecurringInvoice,
  usePauseRecurringInvoice,
  useRecurringInvoices,
  useResumeRecurringInvoice,
  useRunDueRecurringInvoices,
} from "../api/recurring-invoices";

function formatDate(value: string | null) {
  if (!value) {
    return "No programado";
  }
  return new Date(value).toLocaleString("es-DO");
}

export function RecurringInvoicesPage() {
  const [name, setName] = useState("Factura de mantenimiento");
  const [frequency, setFrequency] = useState<RecurringFrequency>("monthly");
  const [customIntervalDays, setCustomIntervalDays] = useState("30");
  const [startAt, setStartAt] = useState(() => new Date().toISOString().slice(0, 16));
  const [endAt, setEndAt] = useState("");
  const [tipoEcf, setTipoEcf] = useState("E31");
  const [rncReceptor, setRncReceptor] = useState("");
  const [total, setTotal] = useState("1500.00");
  const [notes, setNotes] = useState("Servicio recurrente programado desde portal cliente.");
  const [message, setMessage] = useState<string | null>(null);

  const tenantPlanQuery = useTenantPlan();
  const schedulesQuery = useRecurringInvoices();
  const createSchedule = useCreateRecurringInvoice();
  const pauseSchedule = usePauseRecurringInvoice();
  const resumeSchedule = useResumeRecurringInvoice();
  const runDue = useRunDueRecurringInvoices();

  const currentPlan = tenantPlanQuery.data?.current_plan ?? null;
  const recurringIncluded = Boolean(currentPlan?.includes_recurring_invoices);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    try {
      await createSchedule.mutateAsync({
        name: name.trim(),
        frequency,
        customIntervalDays: frequency === "custom" ? Number(customIntervalDays) : null,
        startAt: new Date(startAt).toISOString(),
        endAt: endAt ? new Date(endAt).toISOString() : null,
        tipoEcf,
        rncReceptor: rncReceptor.trim() || null,
        total,
        notes: notes.trim() || null,
      });
      setMessage("Factura recurrente programada correctamente.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo programar la factura recurrente.");
    }
  }

  async function handleRunDue() {
    setMessage(null);
    try {
      const result = await runDue.mutateAsync();
      setMessage(`Procesadas ${result.processed} programaciones. Generadas: ${result.generated}. Fallidas: ${result.failed}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudieron ejecutar las facturas recurrentes vencidas.");
    }
  }

  return (
    <RequirePermission anyOf={["TENANT_RECURRING_INVOICE_MANAGE", "TENANT_INVOICE_EMIT"]}>
      <div className="space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold text-white">Facturas recurrentes</h1>
            <p className="max-w-3xl text-sm text-slate-300">
              Programa facturas diarias, quincenales, mensuales o por rango personalizado para que la plataforma las
              materialice automaticamente cuando llegue su fecha.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void handleRunDue()}
            disabled={!recurringIncluded || runDue.isPending}
            className="rounded-md border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
            data-tour="recurring-run-due"
          >
            Ejecutar vencidas ahora
          </button>
        </header>

        {message ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-200">{message}</div>
        ) : null}

        {!tenantPlanQuery.isLoading && !recurringIncluded ? (
          <div className="rounded-2xl border border-amber-800/60 bg-amber-950/20 p-5 text-sm text-amber-100">
            <p className="font-semibold">Servicio disponible desde Profesional (Pro)</p>
            <p className="mt-2 text-amber-100/80">
              Tu plan actual es <span className="font-semibold">{currentPlan?.name ?? "Sin plan asignado"}</span>. Las
              facturas recurrentes forman parte del paquete Pro en adelante por tratarse de una automatizacion operativa.
            </p>
            <Link
              to="/plans"
              className="mt-3 inline-flex rounded-md border border-amber-700 px-3 py-2 text-xs font-semibold text-amber-100 hover:bg-amber-900/30"
            >
              Ver planes y solicitar upgrade
            </Link>
          </div>
        ) : null}

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <form
            onSubmit={handleSubmit}
            className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6"
            data-tour="recurring-form"
          >
            <fieldset disabled={!recurringIncluded} className="space-y-4 disabled:cursor-not-allowed disabled:opacity-60">
              <div className="space-y-1">
                <h2 className="text-lg font-semibold text-white">Nueva programacion</h2>
                <p className="text-sm text-slate-400">
                  Define la plantilla base y la periodicidad. Para rango personalizado indica el intervalo en dias.
                </p>
              </div>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-200">Nombre interno</span>
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                  required
                />
              </label>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Periodo</span>
                  <select
                    value={frequency}
                    onChange={(event) => setFrequency(event.target.value as RecurringFrequency)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                  >
                    <option value="daily">Diario</option>
                    <option value="biweekly">Quincenal</option>
                    <option value="monthly">Mensual</option>
                    <option value="custom">Personalizado</option>
                  </select>
                </label>

                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Tipo e-CF</span>
                  <input
                    value={tipoEcf}
                    onChange={(event) => setTipoEcf(event.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                    maxLength={3}
                    required
                  />
                </label>
              </div>

              {frequency === "custom" ? (
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Cada cuantos dias</span>
                  <input
                    type="number"
                    min={2}
                    max={365}
                    value={customIntervalDays}
                    onChange={(event) => setCustomIntervalDays(event.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                  />
                </label>
              ) : null}

              <div className="grid gap-4 md:grid-cols-2">
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Inicio</span>
                  <input
                    type="datetime-local"
                    value={startAt}
                    onChange={(event) => setStartAt(event.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                    required
                  />
                </label>

                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Fin opcional</span>
                  <input
                    type="datetime-local"
                    value={endAt}
                    onChange={(event) => setEndAt(event.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                  />
                </label>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">RNC receptor</span>
                  <input
                    value={rncReceptor}
                    onChange={(event) => setRncReceptor(event.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                    placeholder="Opcional"
                  />
                </label>

                <label className="block space-y-2">
                  <span className="text-sm font-medium text-slate-200">Monto total</span>
                  <input
                    value={total}
                    onChange={(event) => setTotal(event.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                    required
                  />
                </label>
              </div>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-200">Notas</span>
                <textarea
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  rows={3}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                />
              </label>

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={createSchedule.isPending || !recurringIncluded}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700"
                >
                  {createSchedule.isPending ? "Programando..." : "Programar factura"}
                </button>
              </div>
            </fieldset>
          </form>

          <section className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6" data-tour="recurring-list">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-white">Programaciones activas</h2>
              <p className="text-sm text-slate-400">
                Revisa la proxima ejecucion, historial corto y pausa o reanuda segun la operacion del cliente.
              </p>
            </div>

            <div className="space-y-3">
              {(schedulesQuery.data ?? []).map((schedule) => (
                <article key={schedule.id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-100">{schedule.name}</h3>
                        <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[11px] uppercase tracking-wide text-slate-300">
                          {schedule.frequency}
                        </span>
                        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary">
                          {schedule.status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">
                        Proxima corrida: {formatDate(schedule.nextRunAt)} - Ultima: {formatDate(schedule.lastRunAt)}
                      </p>
                      <p className="text-xs text-slate-500">
                        {Number(schedule.total).toLocaleString("es-DO", { style: "currency", currency: "DOP" })} - Tipo {schedule.tipoEcf}
                        {schedule.rncReceptor ? ` - Receptor ${schedule.rncReceptor}` : ""}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {schedule.status === "active" ? (
                        <button
                          type="button"
                          onClick={() => void pauseSchedule.mutateAsync(schedule.id)}
                          className="rounded-md border border-amber-700 px-3 py-2 text-xs font-semibold text-amber-200 hover:bg-amber-900/30"
                        >
                          Pausar
                        </button>
                      ) : null}
                      {schedule.status === "paused" ? (
                        <button
                          type="button"
                          onClick={() => void resumeSchedule.mutateAsync(schedule.id)}
                          disabled={!recurringIncluded}
                          className="rounded-md border border-emerald-700 px-3 py-2 text-xs font-semibold text-emerald-200 hover:bg-emerald-900/30 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Reanudar
                        </button>
                      ) : null}
                    </div>
                  </div>

                  {schedule.executions.length > 0 ? (
                    <div className="mt-4 space-y-2 rounded-lg border border-slate-800 bg-slate-950/70 p-3">
                      <p className="text-xs uppercase tracking-wide text-slate-400">Ultimas ejecuciones</p>
                      {schedule.executions.map((execution) => (
                        <div key={execution.id} className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-300">
                          <span>{formatDate(execution.scheduledFor)}</span>
                          <span>{execution.status}</span>
                          <span>{execution.invoiceId ? `Factura #${execution.invoiceId}` : execution.errorMessage ?? "Sin factura"}</span>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </article>
              ))}

              {!schedulesQuery.isLoading && (schedulesQuery.data ?? []).length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-400">
                  Todavia no hay facturas recurrentes programadas.
                </div>
              ) : null}
            </div>
          </section>
        </section>
      </div>
    </RequirePermission>
  );
}
