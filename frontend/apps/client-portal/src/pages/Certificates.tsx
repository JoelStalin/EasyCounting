import { FormEvent, useState } from "react";
import { useTenantCertificates, useUploadTenantCertificate } from "../api/certificates";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";

function formatDate(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export function CertificatesPage() {
  const certificatesQuery = useTenantCertificates();
  const uploadCertificate = useUploadTenantCertificate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [alias, setAlias] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      setError("Selecciona un archivo .p12 o .pfx antes de continuar.");
      return;
    }
    setError(null);
    setMessage(null);
    try {
      const response = await uploadCertificate.mutateAsync({
        alias: alias.trim() || selectedFile.name.replace(/\.(p12|pfx)$/i, ""),
        password,
        certificate: selectedFile,
        activate: true,
      });
      setMessage(response.message);
      setPassword("");
      setSelectedFile(null);
      setAlias(response.alias);
    } catch (mutationError: unknown) {
      const fallback = "No se pudo cargar el certificado.";
      const detail =
        typeof mutationError === "object" &&
        mutationError !== null &&
        "response" in mutationError &&
        typeof (mutationError as { response?: { data?: { detail?: string } } }).response?.data?.detail === "string"
          ? (mutationError as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : fallback;
      setError(detail ?? fallback);
    }
  };

  const items = certificatesQuery.data?.items ?? [];
  const activeSource = certificatesQuery.data?.activeSource ?? null;

  return (
    <RequirePermission anyOf={["TENANT_CERT_UPLOAD"]}>
      <div className="space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold text-white">Certificados digitales</h1>
          <p className="text-sm text-slate-300">Carga el .p12 del emisor y el sistema lo usara para firma automatica.</p>
        </header>

        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-white">Estado de firma automatica</h2>
              <p className="text-sm text-slate-300">
                {activeSource === "tenant"
                  ? "El tenant tiene un certificado activo listo para firmar."
                  : activeSource === "env"
                    ? "No hay certificado cargado por tenant; el backend esta usando el certificado global configurado."
                    : "Aun no existe un certificado utilizable para firma automatica."}
              </p>
            </div>
            {certificatesQuery.isLoading ? <Spinner label="Cargando certificados" /> : null}
          </div>
        </section>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <label className="block space-y-2 text-sm text-slate-300">
            Alias
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              type="text"
              value={alias}
              onChange={(event) => setAlias(event.target.value)}
              placeholder="Certificado DGII principal"
              maxLength={100}
            />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            Seleccionar archivo
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              type="file"
              accept=".p12,.pfx"
              required
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <label className="block space-y-2 text-sm text-slate-300">
            Contraseña
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <div className="flex justify-end">
            <button
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:bg-slate-700"
              type="submit"
              disabled={uploadCertificate.isPending}
            >
              {uploadCertificate.isPending ? <Spinner label="Validando" /> : "Subir y activar"}
            </button>
          </div>
          {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
          {error ? <p className="text-sm text-rose-300">{error}</p> : null}
        </form>

        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <header className="mb-4 space-y-1">
            <h2 className="text-sm font-semibold text-white">Certificados registrados</h2>
            <p className="text-sm text-slate-300">El certificado activo es el que usara la firma automatica del portal DGII.</p>
          </header>
          {certificatesQuery.isError ? (
            <p className="text-sm text-rose-300">No se pudo cargar el listado de certificados.</p>
          ) : null}
          {!certificatesQuery.isLoading && items.length === 0 ? (
            <p className="text-sm text-slate-400">Todavia no hay certificados cargados para este tenant.</p>
          ) : null}
          {items.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-800 text-sm text-slate-200">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                    <th className="px-3 py-2">Alias</th>
                    <th className="px-3 py-2">Subject</th>
                    <th className="px-3 py-2">Issuer</th>
                    <th className="px-3 py-2">Vigencia</th>
                    <th className="px-3 py-2">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900/60">
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td className="px-3 py-3">{item.alias}</td>
                      <td className="px-3 py-3 text-slate-300">{item.subject}</td>
                      <td className="px-3 py-3 text-slate-300">{item.issuer}</td>
                      <td className="px-3 py-3 text-slate-300">
                        {formatDate(item.notBefore)}{" "}
                        <span className="text-slate-500">→</span>{" "}
                        {formatDate(item.notAfter)}
                      </td>
                      <td className="px-3 py-3">
                        <span
                          className={
                            item.isActive
                              ? "rounded-full bg-emerald-950 px-2 py-1 text-xs font-semibold text-emerald-300"
                              : "rounded-full bg-slate-800 px-2 py-1 text-xs font-semibold text-slate-300"
                          }
                        >
                          {item.isActive ? "Activo" : "Registrado"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </div>
    </RequirePermission>
  );
}
