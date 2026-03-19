import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreatePlan } from "../api/plans";

export function PlanEditorPage() {
  const navigate = useNavigate();
  const createPlan = useCreatePlan();
  const [form, setForm] = useState({
    name: "",
    precio_mensual: "0.00",
    precio_por_documento: "0.0000",
    documentos_incluidos: 0,
    max_facturas_mes: 0,
    max_facturas_por_receptor_mes: 0,
    max_monto_por_factura: "0.00",
    includes_recurring_invoices: false,
    descripcion: "",
  });

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await createPlan.mutateAsync({
      name: form.name,
      precio_mensual: form.precio_mensual,
      precio_por_documento: form.precio_por_documento,
      documentos_incluidos: Number(form.documentos_incluidos) || 0,
      max_facturas_mes: Number(form.max_facturas_mes) || 0,
      max_facturas_por_receptor_mes: Number(form.max_facturas_por_receptor_mes) || 0,
      max_monto_por_factura: form.max_monto_por_factura || "0.00",
      includes_recurring_invoices: form.includes_recurring_invoices,
      descripcion: form.descripcion ? form.descripcion : null,
    });
    navigate("/plans");
  };

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Editor de plan tarifario</h1>
        <p className="text-sm text-slate-300">
          Configura valores fijos, porcentajes y tramos escalonados siguiendo las fórmulas descritas en la guía 13.
        </p>
      </header>
      {createPlan.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo guardar el plan.
        </div>
      ) : null}
      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm text-slate-300">
            Nombre del plan
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              placeholder="Plan Mixto Pro"
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-300">
            Incluidos
            <input
              type="number"
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.documentos_incluidos}
              onChange={(e) => setForm((prev) => ({ ...prev, documentos_incluidos: Number(e.target.value) }))}
            />
          </label>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="space-y-2 text-sm text-slate-300">
            Máx. facturas/mes
            <input
              type="number"
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.max_facturas_mes}
              onChange={(e) => setForm((prev) => ({ ...prev, max_facturas_mes: Number(e.target.value) }))}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-300">
            Máx. facturas/cliente/mes
            <input
              type="number"
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.max_facturas_por_receptor_mes}
              onChange={(e) => setForm((prev) => ({ ...prev, max_facturas_por_receptor_mes: Number(e.target.value) }))}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-300">
            Máx. monto por factura (DOP)
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.max_monto_por_factura}
              onChange={(e) => setForm((prev) => ({ ...prev, max_monto_por_factura: e.target.value }))}
            />
          </label>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="space-y-2 text-sm text-slate-300">
            Precio mensual
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.precio_mensual}
              onChange={(e) => setForm((prev) => ({ ...prev, precio_mensual: e.target.value }))}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-300">
            Precio por documento
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.precio_por_documento}
              onChange={(e) => setForm((prev) => ({ ...prev, precio_por_documento: e.target.value }))}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-300">
            Descripción
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              value={form.descripcion}
              onChange={(e) => setForm((prev) => ({ ...prev, descripcion: e.target.value }))}
            />
          </label>
        </div>
        <label className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-950/40 px-4 py-3 text-sm text-slate-200">
          <input
            type="checkbox"
            checked={form.includes_recurring_invoices}
            onChange={(e) => setForm((prev) => ({ ...prev, includes_recurring_invoices: e.target.checked }))}
          />
          Incluir facturas recurrentes en este plan
        </label>
        <div className="flex justify-end gap-2">
          <button type="button" className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-200">
            Cancelar
          </button>
          <button
            type="submit"
            disabled={createPlan.isPending || !form.name}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:bg-slate-700"
          >
            {createPlan.isPending ? "Guardando…" : "Guardar plan"}
          </button>
        </div>
      </form>
    </div>
  );
}
