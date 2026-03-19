import { useMemo } from "react";
import { RequirePermission } from "../auth/guards";
import { usePlans, useRequestPlanChange, useTenantPlan, type Plan } from "../api/plans";

export function PlansPage() {
  const plansQuery = usePlans();
  const tenantPlanQuery = useTenantPlan();
  const requestChange = useRequestPlanChange();

  const currentPlan = tenantPlanQuery.data?.current_plan ?? null;
  const pendingPlan = tenantPlanQuery.data?.pending_plan ?? null;
  const pendingEffective = tenantPlanQuery.data?.pending_effective_at;

  const pendingDateLabel = useMemo(() => {
    if (!pendingEffective) {
      return null;
    }
    return new Date(pendingEffective).toLocaleDateString("es-DO", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }, [pendingEffective]);

  return (
    <RequirePermission anyOf={["TENANT_PLAN_VIEW", "TENANT_PLAN_UPGRADE"]}>
      <div className="space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold text-white">Planes y suscripcion</h1>
          <p className="text-sm text-slate-300">
            El cambio de plan se hace efectivo al finalizar el mes en curso.
          </p>
        </header>

        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-300">
          <p>
            Plan actual:{" "}
            <span className="font-semibold text-primary">
              {tenantPlanQuery.isLoading ? "Cargando..." : currentPlan?.name ?? "Sin plan asignado"}
            </span>
          </p>
          {pendingPlan ? (
            <p className="mt-2">
              Cambio programado:{" "}
              <span className="font-semibold text-amber-200">{pendingPlan.name}</span>
              {pendingDateLabel ? <span className="text-slate-400"> (vigente desde {pendingDateLabel})</span> : null}
            </p>
          ) : null}
        </section>

        {plansQuery.isError || tenantPlanQuery.isError ? (
          <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
            No se pudo cargar la informacion de planes.
          </div>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {(plansQuery.data ?? []).map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              currentPlanId={currentPlan?.id ?? null}
              pendingPlanId={pendingPlan?.id ?? null}
              onSelect={() => requestChange.mutate(plan.id)}
              isLoading={requestChange.isPending}
            />
          ))}
        </div>
      </div>
    </RequirePermission>
  );
}

interface PlanCardProps {
  plan: Plan;
  currentPlanId: number | null;
  pendingPlanId: number | null;
  onSelect: () => void;
  isLoading: boolean;
}

function PlanCard({ plan, currentPlanId, pendingPlanId, onSelect, isLoading }: PlanCardProps) {
  const isCurrent = currentPlanId === plan.id;
  const isPending = pendingPlanId === plan.id;

  let actionLabel = "Solicitar cambio";
  if (isCurrent) {
    actionLabel = "Plan actual";
  } else if (isPending) {
    actionLabel = "Cambio programado";
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-sm text-slate-200">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">{plan.name}</h3>
        <span className="text-sm font-semibold text-primary">
          {Number(plan.precio_mensual).toLocaleString("es-DO", { style: "currency", currency: "DOP" })} / mes
        </span>
      </div>
      {plan.descripcion ? <p className="mt-2 text-xs text-slate-400">{plan.descripcion}</p> : null}
      <div className="mt-4 grid gap-2 text-xs text-slate-300">
        <p>Documentos incluidos: {plan.documentos_incluidos}</p>
        <p>Precio por documento: {Number(plan.precio_por_documento).toLocaleString("es-DO", { style: "currency", currency: "DOP" })}</p>
        <p>Max facturas/mes: {plan.max_facturas_mes}</p>
        <p>Max facturas/cliente/mes: {plan.max_facturas_por_receptor_mes}</p>
        <p>Monto max por factura: {Number(plan.max_monto_por_factura).toLocaleString("es-DO", { style: "currency", currency: "DOP" })}</p>
        <p>
          Facturas recurrentes:{" "}
          <span className={plan.includes_recurring_invoices ? "text-emerald-300" : "text-amber-200"}>
            {plan.includes_recurring_invoices ? "Incluidas" : "No incluidas"}
          </span>
        </p>
      </div>
      <button
        type="button"
        onClick={onSelect}
        disabled={isLoading || isCurrent || isPending}
        className="mt-4 w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:bg-slate-700"
      >
        {isLoading ? "Procesando..." : actionLabel}
      </button>
    </div>
  );
}
