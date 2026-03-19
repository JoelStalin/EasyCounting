import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { RequirePermission } from "../auth/guards";
import { useTenantChat } from "../api/chat";

const SUGGESTIONS = [
  "Cual es el estado del ultimo comprobante emitido?",
  "Cuantos comprobantes aceptados tengo este mes?",
  "Dame detalles del comprobante E310000000001",
];

export function AssistantPage() {
  const [question, setQuestion] = useState(SUGGESTIONS[0]);
  const chat = useTenantChat();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = question.trim();
    if (!normalized) {
      return;
    }
    await chat.mutateAsync({ question: normalized, max_sources: 4 });
  };

  return (
    <RequirePermission anyOf={["TENANT_CHAT_ASSIST"]}>
      <div className="space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold text-white">Asistente de comprobantes</h1>
          <p className="max-w-3xl text-sm text-slate-300">
            Este chatbot solo responde con informacion del tenant autenticado. No puede acceder a comprobantes,
            facturas ni datos de otras empresas o clientes.
          </p>
          <p className="max-w-3xl text-xs text-slate-500">
            Las consultas operativas se preprocesan y, cuando es posible, se resuelven localmente antes de consumir
            creditos del proveedor IA.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.9fr)]">
          <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
            <label className="block space-y-2">
              <span className="text-sm font-medium text-slate-100">Pregunta</span>
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={7}
                className="w-full rounded-xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-primary"
                placeholder="Ejemplo: Cual fue el ultimo comprobante rechazado y su track ID?"
              />
            </label>

            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setQuestion(suggestion)}
                  className="rounded-full border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:border-primary hover:text-primary"
                >
                  {suggestion}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={chat.isPending}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:opacity-60"
              >
                {chat.isPending ? "Consultando..." : "Preguntar al asistente"}
              </button>
              <span className="text-xs text-slate-400">Motor activo: {chat.data?.engine ?? "local"}</span>
            </div>

            {chat.isError ? (
              <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
                No se pudo procesar la consulta del asistente.
              </div>
            ) : null}

            {chat.data?.preprocess ? (
              <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-xs text-slate-300">
                <p>
                  <span className="font-semibold text-slate-100">Preproceso:</span>{" "}
                  {chat.data.preprocess.dispatchStrategy === "local_only"
                    ? "resuelta localmente antes de consumir creditos"
                    : "escalada al proveedor IA"}
                </p>
                <p>
                  <span className="font-semibold text-slate-100">Intencion detectada:</span>{" "}
                  {chat.data.preprocess.intent}
                </p>
                <p>
                  <span className="font-semibold text-slate-100">Consulta normalizada:</span>{" "}
                  {chat.data.preprocess.normalizedQuestion}
                </p>
              </div>
            ) : null}
          </form>

          <aside className="space-y-4 rounded-2xl border border-slate-800 bg-slate-950/50 p-6">
            <h2 className="text-lg font-semibold text-white">Respuesta</h2>
            <p className="text-sm leading-7 text-slate-200">
              {chat.data?.answer ?? "Todavia no hay respuesta. Haz una pregunta sobre tus comprobantes."}
            </p>

            {chat.data?.warnings?.length ? (
              <div className="rounded-xl border border-amber-900/60 bg-amber-950/30 p-4 text-xs text-amber-200">
                {chat.data.warnings.join(" ")}
              </div>
            ) : null}

            <div className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Fuentes usadas</h3>
              {chat.data?.sources?.length ? (
                chat.data.sources.map((source) => (
                  <div key={source.invoice_id} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <Link className="text-sm font-semibold text-primary" to={`/invoices/${source.invoice_id}`}>
                        {source.encf}
                      </Link>
                      <span className="rounded-full border border-slate-700 px-2 py-1 text-[11px] text-slate-300">
                        {source.estado_dgii}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-300">{source.snippet}</p>
                    <p className="mt-2 text-[11px] text-slate-500">
                      Track: {source.track_id ?? "N/A"} · Fecha: {new Date(source.fecha_emision).toLocaleString()}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">El asistente mostrara aqui las facturas usadas para responder.</p>
              )}
            </div>
          </aside>
        </section>
      </div>
    </RequirePermission>
  );
}
