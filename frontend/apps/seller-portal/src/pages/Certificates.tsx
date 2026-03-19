import { FormEvent, useState } from "react";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";

export function CertificatesPage() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setMessage("Certificado cargado y validado (simulado).");
    }, 800);
  };

  return (
    <RequirePermission anyOf={["TENANT_CERT_UPLOAD"]}>
      <div className="space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold text-white">Certificados digitales</h1>
          <p className="text-sm text-slate-300">Sube archivos .p12 y valida vigencia, issuer y subject.</p>
        </header>
        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <label className="block space-y-2 text-sm text-slate-300">
            Seleccionar archivo
            <input className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" type="file" accept=".p12" required />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            Contraseña
            <input className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2" type="password" required />
          </label>
          <div className="flex justify-end">
            <button
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
              type="submit"
              disabled={loading}
            >
              {loading ? <Spinner label="Validando" /> : "Subir"}
            </button>
          </div>
        </form>
        {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      </div>
    </RequirePermission>
  );
}
