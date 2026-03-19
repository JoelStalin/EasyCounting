import { FormEvent, useMemo, useState } from "react";
import { RequirePermission } from "../auth/guards";
import { useInvoices } from "../api/invoices";
import {
  TenantApiAccessMode,
  useCreateTenantApiToken,
  useRevokeTenantApiToken,
  useTenantApiTokens,
} from "../api/tenant-api";

function resolveEnterpriseApiBaseUrl(): string {
  const { hostname } = window.location;
  if (hostname === "127.0.0.1" || hostname === "localhost") {
    return "http://127.0.0.1:28080";
  }
  if (hostname === "getupsoft.com.do" || hostname.endsWith(".getupsoft.com.do")) {
    return "https://api.getupsoft.com.do";
  }
  return window.location.origin;
}

function formatDate(value: string | null) {
  if (!value) {
    return "Nunca";
  }
  return new Date(value).toLocaleString("es-DO");
}

function buildExampleCurl(baseUrl: string) {
  return [
    "curl -X POST \\",
    `  "${baseUrl}/api/v1/tenant-api/invoices" \\`,
    "  -H \"Authorization: Bearer <TOKEN_EMPRESARIAL>\" \\",
    "  -H \"Content-Type: application/json\" \\",
    "  -d '{",
    "    \"encf\": \"E310000000123\",",
    "    \"tipoEcf\": \"E31\",",
    "    \"rncReceptor\": \"131415161\",",
    "    \"total\": \"1500.00\"",
    "  }'",
  ].join("\n");
}

export function OdooIntegrationPage() {
  const [name, setName] = useState("Odoo ERP principal");
  const [accessMode, setAccessMode] = useState<TenantApiAccessMode>("read_write");
  const [expiresInDays, setExpiresInDays] = useState("365");
  const [latestToken, setLatestToken] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const tokensQuery = useTenantApiTokens();
  const createToken = useCreateTenantApiToken();
  const revokeToken = useRevokeTenantApiToken();
  const invoicesQuery = useInvoices({ page: 1, size: 5 });

  const apiBaseUrl = useMemo(() => resolveEnterpriseApiBaseUrl(), []);
  const exampleCurl = useMemo(() => buildExampleCurl(apiBaseUrl), [apiBaseUrl]);

  async function handleCreateToken(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setLatestToken(null);
    try {
      const response = await createToken.mutateAsync({
        name: name.trim(),
        accessMode,
        expiresInDays: expiresInDays.trim() ? Number(expiresInDays) : null,
      });
      setLatestToken(response.token);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo generar el token API.");
    }
  }

  async function handleRevoke(tokenId: number) {
    setErrorMessage(null);
    try {
      await revokeToken.mutateAsync(tokenId);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo revocar el token API.");
    }
  }

  async function handleCopyToken() {
    if (!latestToken) {
      return;
    }
    await navigator.clipboard.writeText(latestToken);
  }

  return (
    <RequirePermission anyOf={["TENANT_API_TOKEN_MANAGE"]}>
      <div className="space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold text-white">API Odoo para clientes empresariales</h1>
          <p className="max-w-3xl text-sm text-slate-300">
            Genera tokens API para que tu ERP Odoo consulte facturas, valide estados y registre comprobantes desde una
            integracion segura por tenant. Cada token queda aislado a tu empresa.
          </p>
        </header>

        {errorMessage ? (
          <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">{errorMessage}</div>
        ) : null}

        {latestToken ? (
          <section className="rounded-2xl border border-emerald-800/60 bg-emerald-950/20 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-emerald-200">Token generado</h2>
                <p className="text-sm text-emerald-100/80">
                  Este valor solo se muestra una vez. Copialo y guardalo en Odoo inmediatamente.
                </p>
              </div>
              <button
                type="button"
                onClick={() => void handleCopyToken()}
                className="rounded-md border border-emerald-700 px-3 py-2 text-xs font-semibold text-emerald-100 hover:bg-emerald-900/40"
              >
                Copiar token
              </button>
            </div>
            <textarea
              readOnly
              value={latestToken}
              rows={3}
              className="mt-4 w-full rounded-xl border border-emerald-900/60 bg-slate-950/70 px-3 py-3 font-mono text-sm text-emerald-100"
            />
          </section>
        ) : null}

        <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
          <form
            onSubmit={handleCreateToken}
            className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6"
            data-tour="api-token-form"
          >
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-white">Generar token empresarial</h2>
              <p className="text-sm text-slate-400">
                Usa un token por integracion para revocar accesos sin afectar otros sistemas.
              </p>
            </div>

            <label className="block space-y-2">
              <span className="text-sm font-medium text-slate-200">Nombre de la integracion</span>
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="Odoo ERP principal"
                required
              />
            </label>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-200">Acceso</span>
                <select
                  value={accessMode}
                  onChange={(event) => setAccessMode(event.target.value as TenantApiAccessMode)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                >
                  <option value="read">Solo lectura</option>
                  <option value="read_write">Lectura y registro</option>
                </select>
              </label>

              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-200">Expira en dias</span>
                <input
                  value={expiresInDays}
                  onChange={(event) => setExpiresInDays(event.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                  min={1}
                  max={3650}
                  type="number"
                />
              </label>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-300">
              <p className="font-medium text-slate-100">Scopes que recibira el token</p>
              <ul className="mt-2 space-y-1 text-slate-400">
                <li>`invoices:read` para consultar listados y detalles.</li>
                <li>`invoices:write` solo si quieres registrar facturas desde Odoo.</li>
              </ul>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={createToken.isPending}
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700"
              >
                {createToken.isPending ? "Generando..." : "Generar token"}
              </button>
            </div>
          </form>

          <section className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6" data-tour="api-endpoints">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-white">Endpoints para Odoo</h2>
              <p className="text-sm text-slate-400">
                Esta base URL debe configurarse en tu cliente ERP para consumir el API empresarial por tenant.
              </p>
            </div>

            <div className="space-y-3 text-sm">
              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">Base URL</p>
                <p className="mt-2 break-all font-mono text-slate-100">{apiBaseUrl}</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">Consultar facturas</p>
                <p className="mt-2 break-all font-mono text-slate-100">{apiBaseUrl}/api/v1/tenant-api/invoices</p>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">Registrar factura</p>
                <p className="mt-2 break-all font-mono text-slate-100">{apiBaseUrl}/api/v1/tenant-api/invoices</p>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
              <p className="mb-3 text-xs uppercase tracking-wide text-slate-400">Ejemplo curl</p>
              <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-slate-200">{exampleCurl}</pre>
            </div>
          </section>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6" data-tour="api-token-list">
          <div>
            <h2 className="text-lg font-semibold text-white">Tokens emitidos</h2>
            <p className="text-sm text-slate-400">Revoca cualquier token comprometido sin cerrar la sesion del portal.</p>
          </div>

          <div className="mt-4 space-y-3">
            {(tokensQuery.data ?? []).map((token) => (
              <article key={token.id} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-semibold text-slate-100">{token.name}</h3>
                      {token.revokedAt ? (
                        <span className="rounded-full bg-rose-500/15 px-2 py-0.5 text-[11px] font-semibold text-rose-300">
                          Revocado
                        </span>
                      ) : (
                        <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-300">
                          Activo
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400">
                      Prefijo: <span className="font-mono text-slate-200">{token.tokenPrefix}</span>
                      {" · "}Scopes: <span className="text-slate-200">{token.scopes.join(", ")}</span>
                    </p>
                    <p className="text-xs text-slate-500">
                      Creado: {formatDate(token.createdAt)} · Ultimo uso: {formatDate(token.lastUsedAt)} · Expira:{" "}
                      {formatDate(token.expiresAt)}
                    </p>
                  </div>
                  {!token.revokedAt ? (
                    <button
                      type="button"
                      onClick={() => void handleRevoke(token.id)}
                      disabled={revokeToken.isPending}
                      className="rounded-md border border-rose-800 px-3 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-900/40"
                    >
                      Revocar
                    </button>
                  ) : null}
                </div>
              </article>
            ))}

            {!tokensQuery.isLoading && (tokensQuery.data ?? []).length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-400">
                Todavia no hay tokens API emitidos para este tenant.
              </div>
            ) : null}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-white">Ultimos comprobantes visibles por el cliente</h2>
            <p className="text-sm text-slate-400">
              Esta vista te deja validar rapidamente que la integracion Odoo y el portal observan el mismo tenant.
            </p>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-800 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
                  <th className="pb-3 pr-4 font-medium">ENCF</th>
                  <th className="pb-3 pr-4 font-medium">Tipo</th>
                  <th className="pb-3 pr-4 font-medium">Estado</th>
                  <th className="pb-3 pr-4 font-medium">Total</th>
                  <th className="pb-3 font-medium">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-900/80">
                {(invoicesQuery.data?.items ?? []).map((invoice) => (
                  <tr key={invoice.id} className="text-slate-200">
                    <td className="py-3 pr-4 font-mono text-xs">{invoice.encf}</td>
                    <td className="py-3 pr-4">{invoice.tipo_ecf}</td>
                    <td className="py-3 pr-4">{invoice.estado_dgii}</td>
                    <td className="py-3 pr-4">
                      {Number(invoice.total).toLocaleString("es-DO", { style: "currency", currency: "DOP" })}
                    </td>
                    <td className="py-3">{new Date(invoice.fecha_emision).toLocaleString("es-DO")}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!invoicesQuery.isLoading && (invoicesQuery.data?.items.length ?? 0) === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-400">
                No hay comprobantes recientes para mostrar en este tenant.
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </RequirePermission>
  );
}
