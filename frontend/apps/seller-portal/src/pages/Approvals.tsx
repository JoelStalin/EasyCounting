import { FormEvent, useState } from "react";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";

export function ApprovalsPage() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setMessage("ARECF enviado correctamente (simulado).");
    }, 800);
  };

  return (
    <RequirePermission anyOf={["TENANT_APPROVAL_SEND"]}>
      <div className="space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold text-white">Aprobaciones y acuses</h1>
          <p className="text-sm text-slate-300">Gestiona ARECF y ACECF siguiendo los motivos autorizados por DGII.</p>
        </header>
        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="grid gap-4 md:grid-cols-3">
            <label className="space-y-2 text-sm text-slate-300">
              ENCF
              <input className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" required />
            </label>
            <label className="space-y-2 text-sm text-slate-300">
              Tipo
              <select className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2">
                <option value="ARECF">ARECF</option>
                <option value="ACECF">ACECF</option>
              </select>
            </label>
            <label className="space-y-2 text-sm text-slate-300">
              Estado
              <select className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2">
                <option value="0">Recibido</option>
                <option value="1">No recibido</option>
              </select>
            </label>
          </div>
          <label className="space-y-2 text-sm text-slate-300">
            Motivo / detalle
            <textarea className="h-24 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
          </label>
          <div className="flex justify-end">
            <button
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
              type="submit"
              disabled={loading}
            >
              {loading ? <Spinner label="Enviando" /> : "Enviar"}
            </button>
          </div>
        </form>
        {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      </div>
    </RequirePermission>
  );
}
