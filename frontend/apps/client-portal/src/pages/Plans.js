import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo } from "react";
import { RequirePermission } from "../auth/guards";
import { usePlans, useRequestPlanChange, useTenantPlan } from "../api/plans";
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
    return (_jsx(RequirePermission, { anyOf: ["TENANT_PLAN_VIEW", "TENANT_PLAN_UPGRADE"], children: _jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-2", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Planes y suscripcion" }), _jsx("p", { className: "text-sm text-slate-300", children: "El cambio de plan se hace efectivo al finalizar el mes en curso." })] }), _jsxs("section", { className: "rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-300", children: [_jsxs("p", { children: ["Plan actual:", " ", _jsx("span", { className: "font-semibold text-primary", children: tenantPlanQuery.isLoading ? "Cargando..." : currentPlan?.name ?? "Sin plan asignado" })] }), pendingPlan ? (_jsxs("p", { className: "mt-2", children: ["Cambio programado:", " ", _jsx("span", { className: "font-semibold text-amber-200", children: pendingPlan.name }), pendingDateLabel ? _jsxs("span", { className: "text-slate-400", children: [" (vigente desde ", pendingDateLabel, ")"] }) : null] })) : null] }), plansQuery.isError || tenantPlanQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar la informacion de planes." })) : null, _jsx("div", { className: "grid gap-4 lg:grid-cols-2", children: (plansQuery.data ?? []).map((plan) => (_jsx(PlanCard, { plan: plan, currentPlanId: currentPlan?.id ?? null, pendingPlanId: pendingPlan?.id ?? null, onSelect: () => requestChange.mutate(plan.id), isLoading: requestChange.isPending }, plan.id))) })] }) }));
}
function PlanCard({ plan, currentPlanId, pendingPlanId, onSelect, isLoading }) {
    const isCurrent = currentPlanId === plan.id;
    const isPending = pendingPlanId === plan.id;
    let actionLabel = "Solicitar cambio";
    if (isCurrent) {
        actionLabel = "Plan actual";
    }
    else if (isPending) {
        actionLabel = "Cambio programado";
    }
    return (_jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-900/40 p-5 text-sm text-slate-200", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h3", { className: "text-lg font-semibold text-white", children: plan.name }), _jsxs("span", { className: "text-sm font-semibold text-primary", children: [Number(plan.precio_mensual).toLocaleString("es-DO", { style: "currency", currency: "DOP" }), " / mes"] })] }), plan.descripcion ? _jsx("p", { className: "mt-2 text-xs text-slate-400", children: plan.descripcion }) : null, _jsxs("div", { className: "mt-4 grid gap-2 text-xs text-slate-300", children: [_jsxs("p", { children: ["Documentos incluidos: ", plan.documentos_incluidos] }), _jsxs("p", { children: ["Precio por documento: ", Number(plan.precio_por_documento).toLocaleString("es-DO", { style: "currency", currency: "DOP" })] }), _jsxs("p", { children: ["Max facturas/mes: ", plan.max_facturas_mes] }), _jsxs("p", { children: ["Max facturas/cliente/mes: ", plan.max_facturas_por_receptor_mes] }), _jsxs("p", { children: ["Monto max por factura: ", Number(plan.max_monto_por_factura).toLocaleString("es-DO", { style: "currency", currency: "DOP" })] }), _jsxs("p", { children: ["Facturas recurrentes:", " ", _jsx("span", { className: plan.includes_recurring_invoices ? "text-emerald-300" : "text-amber-200", children: plan.includes_recurring_invoices ? "Incluidas" : "No incluidas" })] })] }), _jsx("button", { type: "button", onClick: onSelect, disabled: isLoading || isCurrent || isPending, className: "mt-4 w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:bg-slate-700", children: isLoading ? "Procesando..." : actionLabel })] }));
}
