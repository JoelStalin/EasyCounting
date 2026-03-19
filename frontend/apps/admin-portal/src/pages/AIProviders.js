import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { useAIProviders, useCreateAIProvider, useDeleteAIProvider, useUpdateAIProvider, } from "../api/ai-providers";
const PROVIDER_OPTIONS = [
    { value: "openai", label: "ChatGPT / OpenAI", helper: "Proveedor oficial de OpenAI para asistentes y chat." },
    { value: "gemini", label: "Google Gemini", helper: "Proveedor oficial Gemini mediante Google AI Studio / Gemini API." },
    { value: "openai_compatible", label: "OpenAI Compatible", helper: "Motores cloud compatibles con el esquema chat completions." },
];
const EMPTY_FORM = {
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
function Field({ label, children, helper, className = "", }) {
    return (_jsxs("label", { className: `block space-y-2 ${className}`, children: [_jsx("span", { className: "text-sm font-medium text-slate-200", children: label }), children, helper ? _jsx("span", { className: "block text-xs text-slate-500", children: helper }) : null] }));
}
function toFormState(provider) {
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
function parseExtraHeaders(text) {
    const raw = text.trim();
    if (!raw) {
        return null;
    }
    const decoded = JSON.parse(raw);
    if (!decoded || typeof decoded !== "object" || Array.isArray(decoded)) {
        throw new Error("Las cabeceras extra deben ser un objeto JSON.");
    }
    const headers = {};
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
    const [selectedId, setSelectedId] = useState(null);
    const [form, setForm] = useState(EMPTY_FORM);
    const [errorMessage, setErrorMessage] = useState(null);
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
    function updateForm(key, value) {
        setForm((current) => ({ ...current, [key]: value }));
    }
    async function handleSubmit(event) {
        event.preventDefault();
        setErrorMessage(null);
        let payload;
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
        }
        catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "No se pudieron interpretar las cabeceras extra.");
            return;
        }
        try {
            if (selectedId) {
                await updateProvider.mutateAsync(payload);
            }
            else {
                const created = await createProvider.mutateAsync(payload);
                setSelectedId(created.id);
            }
            setForm((current) => ({ ...current, apiKey: "", clearApiKey: false }));
        }
        catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "No se pudo guardar la configuracion.");
        }
    }
    async function handleDelete(providerId) {
        setErrorMessage(null);
        try {
            await deleteProvider.mutateAsync(providerId);
            if (selectedId === providerId) {
                setSelectedId(null);
                setForm(EMPTY_FORM);
            }
        }
        catch (error) {
            setErrorMessage(error instanceof Error ? error.message : "No se pudo eliminar el proveedor.");
        }
    }
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "space-y-2", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Agentes IA cloud" }), _jsx("p", { className: "max-w-3xl text-sm text-slate-300", children: "Configura proveedores globales como ChatGPT, Gemini y motores compatibles desde el panel de plataforma. Esta vista solo debe usarse por superroot porque administra credenciales cloud compartidas." })] }), _jsxs("section", { className: "grid gap-6 xl:grid-cols-[1.15fr_0.85fr]", children: [_jsxs("div", { className: "space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: "Proveedores registrados" }), _jsx("p", { className: "text-sm text-slate-400", children: "Solo uno debe quedar como predeterminado para el chatbot tenant-scoped." })] }), _jsx("button", { type: "button", onClick: () => {
                                            setSelectedId(null);
                                            setForm(EMPTY_FORM);
                                            setErrorMessage(null);
                                        }, className: "rounded-md border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary", children: "Nuevo proveedor" })] }), providersQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar la configuracion de proveedores IA." })) : null, _jsxs("div", { className: "space-y-3", children: [(providersQuery.data ?? []).map((provider) => {
                                        const active = provider.id === selectedId;
                                        return (_jsx("article", { className: `rounded-xl border p-4 transition ${active ? "border-primary/60 bg-primary/10" : "border-slate-800 bg-slate-950/50"}`, children: _jsxs("div", { className: "flex flex-wrap items-start justify-between gap-3", children: [_jsxs("div", { className: "space-y-1", children: [_jsxs("div", { className: "flex flex-wrap items-center gap-2", children: [_jsx("h3", { className: "text-sm font-semibold text-slate-100", children: provider.displayName }), _jsx("span", { className: "rounded-full border border-slate-700 px-2 py-0.5 text-[11px] uppercase tracking-wide text-slate-300", children: provider.providerType }), provider.isDefault ? (_jsx("span", { className: "rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-300", children: "Predeterminado" })) : null, !provider.enabled ? (_jsx("span", { className: "rounded-full bg-amber-500/15 px-2 py-0.5 text-[11px] font-semibold text-amber-300", children: "Inactivo" })) : null] }), _jsxs("p", { className: "text-xs text-slate-400", children: ["Modelo: ", _jsx("span", { className: "text-slate-300", children: provider.model }), " · ", "API key: ", _jsx("span", { className: "text-slate-300", children: provider.apiKeyMasked ?? "no configurada" })] }), _jsxs("p", { className: "text-xs text-slate-500", children: ["Actualizado: ", new Date(provider.updatedAt).toLocaleString()] })] }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("button", { type: "button", onClick: () => {
                                                                    setSelectedId(provider.id);
                                                                    setErrorMessage(null);
                                                                }, className: "rounded-md border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary", children: "Editar" }), _jsx("button", { type: "button", onClick: () => void handleDelete(provider.id), className: "rounded-md border border-rose-800 px-3 py-2 text-xs font-semibold text-rose-200 hover:bg-rose-900/40", disabled: deleteProvider.isPending, children: "Eliminar" })] })] }) }, provider.id));
                                    }), !providersQuery.isLoading && (providersQuery.data ?? []).length === 0 ? (_jsx("div", { className: "rounded-xl border border-dashed border-slate-800 p-6 text-sm text-slate-400", children: "Todavia no hay proveedores IA registrados." })) : null] })] }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4 rounded-2xl border border-slate-800 bg-slate-900/40 p-6", children: [_jsxs("div", { className: "space-y-1", children: [_jsx("h2", { className: "text-lg font-semibold text-white", children: selectedProvider ? `Editar ${selectedProvider.displayName}` : "Crear proveedor" }), _jsx("p", { className: "text-sm text-slate-400", children: currentProviderOption?.helper ?? "Completa el proveedor cloud y marca uno como predeterminado para el chatbot." })] }), errorMessage ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: errorMessage })) : null, _jsxs("div", { className: "grid gap-4 md:grid-cols-2", children: [_jsx(Field, { label: "Nombre visible", children: _jsx("input", { value: form.displayName, onChange: (event) => updateForm("displayName", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "ChatGPT corporativo", required: true }) }), _jsx(Field, { label: "Proveedor", children: _jsx("select", { value: form.providerType, onChange: (event) => updateForm("providerType", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", children: PROVIDER_OPTIONS.map((option) => (_jsx("option", { value: option.value, children: option.label }, option.value))) }) }), _jsx(Field, { label: "Modelo", children: _jsx("input", { value: form.model, onChange: (event) => updateForm("model", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "Modelo a usar por el chatbot", required: true }) }), _jsx(Field, { label: "API key", helper: selectedProvider
                                            ? `Deja en blanco para conservar la actual (${selectedProvider.apiKeyMasked ?? "sin clave"}).`
                                            : "Se almacena cifrada y nunca se vuelve a exponer completa en la UI.", children: _jsx("input", { value: form.apiKey, onChange: (event) => updateForm("apiKey", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "sk-...", type: "password" }) }), _jsx(Field, { label: "Base URL", helper: "Opcional. Si se deja vacio se usa el endpoint oficial por defecto cuando existe.", children: _jsx("input", { value: form.baseUrl, onChange: (event) => updateForm("baseUrl", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "https://api.openai.com/v1" }) }), _jsx(Field, { label: "Timeout (segundos)", children: _jsx("input", { value: form.timeoutSeconds, onChange: (event) => updateForm("timeoutSeconds", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", min: 2, max: 120, step: 1, type: "number" }) }), _jsx(Field, { label: "Organization ID", children: _jsx("input", { value: form.organizationId, onChange: (event) => updateForm("organizationId", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "Solo si el proveedor lo requiere" }) }), _jsx(Field, { label: "Project ID", children: _jsx("input", { value: form.projectId, onChange: (event) => updateForm("projectId", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "Solo si el proveedor lo requiere" }) }), _jsx(Field, { label: "API version", children: _jsx("input", { value: form.apiVersion, onChange: (event) => updateForm("apiVersion", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "Para variantes que versionan la API" }) }), _jsx(Field, { label: "Max completion tokens", children: _jsx("input", { value: form.maxCompletionTokens, onChange: (event) => updateForm("maxCompletionTokens", event.target.value), className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", min: 64, max: 4000, step: 1, type: "number" }) }), _jsx(Field, { label: "Prompt de sistema", className: "md:col-span-2", children: _jsx("textarea", { value: form.systemPrompt, onChange: (event) => updateForm("systemPrompt", event.target.value), rows: 4, className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "Instrucciones globales del asistente para los tenants" }) }), _jsx(Field, { label: "Cabeceras extra JSON", className: "md:col-span-2", helper: 'Ejemplo: {"OpenAI-Project":"proj_123"}', children: _jsx("textarea", { value: form.extraHeadersText, onChange: (event) => updateForm("extraHeadersText", event.target.value), rows: 4, className: "w-full rounded-lg border border-slate-700 bg-slate-950/70 px-3 py-2 font-mono text-sm text-slate-100 focus:border-primary focus:outline-none", placeholder: "{}" }) })] }), _jsxs("div", { className: "grid gap-3 rounded-xl border border-slate-800 bg-slate-950/40 p-4 text-sm text-slate-300", children: [_jsxs("label", { className: "flex items-center gap-3", children: [_jsx("input", { checked: form.enabled, onChange: (event) => updateForm("enabled", event.target.checked), className: "h-4 w-4 rounded border-slate-700 bg-slate-900 text-primary", type: "checkbox" }), "Habilitar proveedor para uso en runtime"] }), _jsxs("label", { className: "flex items-center gap-3", children: [_jsx("input", { checked: form.isDefault, onChange: (event) => updateForm("isDefault", event.target.checked), className: "h-4 w-4 rounded border-slate-700 bg-slate-900 text-primary", type: "checkbox" }), "Usar como proveedor predeterminado del chatbot"] }), selectedProvider ? (_jsxs("label", { className: "flex items-center gap-3", children: [_jsx("input", { checked: form.clearApiKey, onChange: (event) => updateForm("clearApiKey", event.target.checked), className: "h-4 w-4 rounded border-slate-700 bg-slate-900 text-primary", type: "checkbox" }), "Limpiar la API key almacenada"] })) : null] }), _jsxs("div", { className: "flex flex-wrap items-center justify-end gap-3", children: [selectedProvider ? (_jsx("button", { type: "button", onClick: () => {
                                            setSelectedId(null);
                                            setForm(EMPTY_FORM);
                                            setErrorMessage(null);
                                        }, className: "rounded-md border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 hover:border-primary hover:text-primary", children: "Cancelar edicion" })) : null, _jsx("button", { type: "submit", className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:bg-slate-700", disabled: createProvider.isPending || updateProvider.isPending, children: createProvider.isPending || updateProvider.isPending
                                            ? "Guardando..."
                                            : selectedProvider
                                                ? "Guardar proveedor"
                                                : "Crear proveedor" })] })] })] })] }));
}
