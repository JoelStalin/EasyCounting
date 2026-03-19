import { FormEvent, type ReactNode, useEffect, useState } from "react";
import {
  AIProvider,
  AIProviderPayload,
  AIProviderType,
  useAIProviders,
  useCreateAIProvider,
  useDeleteAIProvider,
  useUpdateAIProvider,
} from "../api/ai-providers";

const PROVIDER_OPTIONS: Array<{ value: AIProviderType; label: string; helper: string }> = [
  { value: "openai", label: "ChatGPT / OpenAI", helper: "Proveedor oficial de OpenAI para asistentes y chat." },
  { value: "gemini", label: "Google Gemini", helper: "Proveedor oficial Gemini mediante Google AI Studio / Gemini API." },
  { value: "openai_compatible", label: "OpenAI Compatible", helper: "Motores cloud compatibles con el esquema chat completions." },
];

interface ProviderFormState {
  displayName: string;
  providerType: AIProviderType;
  enabled: boolean;
  isDefault: boolean;
  baseUrl: string;
  model: string;
  apiKey: string;
  clearApiKey: boolean;
  organizationId: string;
  projectId: string;
  apiVersion: string;
  systemPrompt: string;
  extraHeadersText: string;
  timeoutSeconds: string;
  maxCompletionTokens: string;
}

const EMPTY_FORM: ProviderFormState = {
  displayName: "",
  providerType: "openai",
  enabled: true,
  isDefault: false,
  baseUrl: "",
  model: "",
  apiKey: "",
  clearApiKey: false,
  organizationId: "",
  projectId: "",
  apiVersion: "",
  systemPrompt: "",
  extraHeadersText: "",
  timeoutSeconds: "20",
  maxCompletionTokens: "500",
};

function Field({
  label,
  children,
  helper,
  className = "",
}: {
  label: string;
  children: ReactNode;
  helper?: string;
  className?: string;
}) {
  return (
    <label className={`block space-y-2 ${className}`}>
      <span className="text-sm font-medium text-slate-200">{label}</span>
      {children}
      {helper ? <span className="block text-xs text-slate-500">{helper}</span> : null}
    </label>
  );
}

function toFormState(provider: AIProvider): ProviderFormState {
  return {
    displayName: provider.displayName,
    providerType: provider.providerType,
    enabled: provider.enabled,
    isDefault: provider.isDefault,
    baseUrl: provider.baseUrl ?? "",
    model: provider.model,
    apiKey: "",
    clearApiKey: false,
    organizationId: provider.organizationId ?? "",
    projectId: provider.projectId ?? "",
    apiVersion: provider.apiVersion ?? "",
    systemPrompt: provider.systemPrompt ?? "",
    extraHeadersText: Object.keys(provider.extraHeaders).length > 0 ? JSON.stringify(provider.extraHeaders, null, 2) : "",
    timeoutSeconds: String(provider.timeoutSeconds),
    maxCompletionTokens: String(provider.maxCompletionTokens),
  };
}

function parseExtraHeaders(text: string): Record<string, string> | null {
  const raw = text.trim();
  if (!raw) {
    return null;
  }
  const decoded = JSON.parse(raw) as unknown;
  if (!decoded || typeof decoded !== "object" || Array.isArray(decoded)) {
    throw new Error("Las cabeceras extra deben ser un objeto JSON.");
  }
  const headers: Record<string, string> = {};
  for (const [key, value] of Object.entries(decoded)) {
    const keyText = String(key).trim();
    const valueText = String(value).trim();
    if (keyText && valueText) {
      headers[keyText] = valueText;
    }
  }
  return headers;
}

export function AIProvidersPage() {
  const providersQuery = useAIProviders();
  const createProvider = useCreateAIProvider();
  const deleteProvider = useDeleteAIProvider();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [form, setForm] = useState<ProviderFormState>(EMPTY_FORM);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const updateProvider = useUpdateAIProvider(selectedId);

  useEffect(() => {
    if (!selectedId) {
      setForm(EMPTY_FORM);
      return;
    }
    const provider = (providersQuery.data ?? []).find((item) => item.id === selectedId);
    if (provider) {
      setForm(toFormState(provider));
    }
  }, [providersQuery.data, selectedId]);

  const selectedProvider = (providersQuery.data ?? []).find((item) => item.id === selectedId) ?? null;
  const currentProviderOption = PROVIDER_OPTIONS.find((option) => option.value === form.providerType);

  function updateForm<K extends keyof ProviderFormState>(key: K, value: ProviderFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    let payload: AIProviderPayload;
    try {
      payload = {
        displayName: form.displayName.trim(),
        providerType: form.providerType,
        enabled: form.enabled,
        isDefault: form.isDefault,
        baseUrl: form.baseUrl.trim() || null,
        model: form.model.trim(),
        apiKey: form.apiKey.trim() || undefined,
        clearApiKey: form.clearApiKey,
        organizationId: form.organizationId.trim() || null,
        projectId: form.projectId.trim() || null,
        apiVersion: form.apiVersion.trim() || null,
        systemPrompt: form.systemPrompt.trim() || null,
        extraHeaders: parseExtraHeaders(form.extraHeadersText),
        timeoutSeconds: Number(form.timeoutSeconds),
        maxCompletionTokens: Number(form.maxCompletionTokens),
      };
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudieron interpretar las cabeceras extra.");
      return;
    }

    try {
      if (selectedId) {
        await updateProvider.mutateAsync(payload);
      } else {
        const created = await createProvider.mutateAsync(payload);
        setSelectedId(created.id);
      }
      setForm((current) => ({ ...current, apiKey: "", clearApiKey: false }));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo guardar la configuracion.");
    }
  }

  async function handleDelete(providerId: number) {
    setErrorMessage(null);
    try {
      await deleteProvider.mutateAsync(providerId);
      if (selectedId === providerId) {
        setSelectedId(null);
        setForm(EMPTY_FORM);
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo eliminar el proveedor.");
    }
  }

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-white">Agentes IA cloud</h1>
        <p className="max-w-3xl text-sm text-slate-300">
          Configura proveedores globales como ChatGPT, Gemini y motores compatibles desde el panel de plataforma. Esta vista
          solo debe usarse por superroot porque administra credenciales cloud compartidas.
        </p>
      </header>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Proveedores registrados</h2>
              <p className="text-sm text-slate-400">Solo uno debe quedar como predeterminado para el chatbot tenant-scoped.</p>
            </div>
            <button
              type="button"
              onClick={() => {
                setSelectedId(null);
                setForm(EMPTY_FORM);
                setErrorMessage(null);
              }}
              className="rounded-md border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary"
            >
              Nuevo proveedor
            </button>
          </div>

          {providersQuery.isError ? (
            <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
              No se pudo cargar la configuracion de proveedores IA.
            </div>
          ) : null}

          <div className="space-y-3">
            {(providersQuery.data ?? []).map((provider) => {
              const active = provider.id === selectedId;
              return (
                <article
                  key={provider.id}
                  className={`rounded-xl border p-4 transition ${
                    active ? "border-primary/60 bg-primary/10" : "border-slate-800 bg-slate-950/50"
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-100">{provider.displayName}</h3>
                        <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[11px] uppercase tracking-wide text-slate-300">
                          {provider.providerType}
                        </span>
                        {provider.isDefault ? (
                          <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-300">
                            Predeterminado
                          </span>
                        ) : null}
                        {!provider.enabled ? (
                          <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[11px] font-semibold text-amber-300">
                            Inactivo
                          </span>
                        ) : null}
                      </div>
                      <p className="text-xs text-slate-400">
                        Modelo: <span className="text-slate-300">{provider.model}</span>
                        {" · "}API key: <span className="text-slate-300">{provider.apiKeyMasked ?? "no configurada"}</span>
                      </p>
                      <p className="text-xs text-slate-500">
                        Actualizado: {new Date(provider.updatedAt).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedId(provider.id);
                          setErrorMessage(null);
                        }}
                        className="rounded-md border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleDelete(provider.id)}
                        className="rounded-md border border-rose-800 px-3 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-900/40"
                        disabled={deleteProvider.isPending}
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}

            {!providersQuery.isLoading && (providersQuery.data ?? []).length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-400">
                Todavia no hay proveedores IA registrados.
              </div>
            ) : null}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-white">
              {selectedProvider ? `Editar ${selectedProvider.displayName}` : "Crear proveedor"}
            </h2>
            <p className="text-sm text-slate-400">
              {currentProviderOption?.helper ?? "Completa el proveedor cloud y marca uno como predeterminado para el chatbot."}
            </p>
          </div>

          {errorMessage ? (
            <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">{errorMessage}</div>
          ) : null}

          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Nombre visible">
              <input
                value={form.displayName}
                onChange={(event) => updateForm("displayName", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="ChatGPT corporativo"
                required
              />
            </Field>

            <Field label="Proveedor">
              <select
                value={form.providerType}
                onChange={(event) => updateForm("providerType", event.target.value as AIProviderType)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
              >
                {PROVIDER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Modelo">
              <input
                value={form.model}
                onChange={(event) => updateForm("model", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="Modelo a usar por el chatbot"
                required
              />
            </Field>

            <Field
              label="API key"
              helper={
                selectedProvider
                  ? `Deja en blanco para conservar la actual (${selectedProvider.apiKeyMasked ?? "sin clave"}).`
                  : "Se almacena cifrada y nunca se vuelve a exponer completa en la UI."
              }
            >
              <input
                value={form.apiKey}
                onChange={(event) => updateForm("apiKey", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="sk-..."
                type="password"
              />
            </Field>

            <Field label="Base URL" helper="Opcional. Si se deja vacio se usa el endpoint oficial por defecto cuando existe.">
              <input
                value={form.baseUrl}
                onChange={(event) => updateForm("baseUrl", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="https://api.openai.com/v1"
              />
            </Field>

            <Field label="Timeout (segundos)">
              <input
                value={form.timeoutSeconds}
                onChange={(event) => updateForm("timeoutSeconds", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                min={2}
                max={120}
                step={1}
                type="number"
              />
            </Field>

            <Field label="Organization ID">
              <input
                value={form.organizationId}
                onChange={(event) => updateForm("organizationId", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="Solo si el proveedor lo requiere"
              />
            </Field>

            <Field label="Project ID">
              <input
                value={form.projectId}
                onChange={(event) => updateForm("projectId", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="Solo si el proveedor lo requiere"
              />
            </Field>

            <Field label="API version">
              <input
                value={form.apiVersion}
                onChange={(event) => updateForm("apiVersion", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="Para variantes que versionan la API"
              />
            </Field>

            <Field label="Max completion tokens">
              <input
                value={form.maxCompletionTokens}
                onChange={(event) => updateForm("maxCompletionTokens", event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                min={64}
                max={4000}
                step={1}
                type="number"
              />
            </Field>

            <Field label="Prompt de sistema" className="md:col-span-2">
              <textarea
                value={form.systemPrompt}
                onChange={(event) => updateForm("systemPrompt", event.target.value)}
                rows={4}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="Instrucciones globales del asistente para los tenants"
              />
            </Field>

            <Field label="Cabeceras extra JSON" className="md:col-span-2" helper='Ejemplo: {"OpenAI-Project":"proj_123"}'>
              <textarea
                value={form.extraHeadersText}
                onChange={(event) => updateForm("extraHeadersText", event.target.value)}
                rows={4}
                className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 font-mono text-sm text-slate-100 focus:border-primary focus:outline-none"
                placeholder="{}"
              />
            </Field>
          </div>

          <div className="grid gap-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4 text-sm text-slate-300">
            <label className="flex items-center gap-3">
              <input
                checked={form.enabled}
                onChange={(event) => updateForm("enabled", event.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-primary"
                type="checkbox"
              />
              Habilitar proveedor para uso en runtime
            </label>
            <label className="flex items-center gap-3">
              <input
                checked={form.isDefault}
                onChange={(event) => updateForm("isDefault", event.target.checked)}
                className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-primary"
                type="checkbox"
              />
              Usar como proveedor predeterminado del chatbot
            </label>
            {selectedProvider ? (
              <label className="flex items-center gap-3">
                <input
                  checked={form.clearApiKey}
                  onChange={(event) => updateForm("clearApiKey", event.target.checked)}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-primary"
                  type="checkbox"
                />
                Limpiar la API key almacenada
              </label>
            ) : null}
          </div>

          <div className="flex flex-wrap items-center justify-end gap-3">
            {selectedProvider ? (
              <button
                type="button"
                onClick={() => {
                  setSelectedId(null);
                  setForm(EMPTY_FORM);
                  setErrorMessage(null);
                }}
                className="rounded-md border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 hover:border-primary hover:text-primary"
              >
                Cancelar edicion
              </button>
            ) : null}
            <button
              type="submit"
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700"
              disabled={createProvider.isPending || updateProvider.isPending}
            >
              {createProvider.isPending || updateProvider.isPending
                ? "Guardando..."
                : selectedProvider
                  ? "Guardar proveedor"
                  : "Crear proveedor"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
