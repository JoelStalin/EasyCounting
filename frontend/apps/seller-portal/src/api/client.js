import { createApiClient } from "@getupsoft/api-client";
import { useAuthStore } from "../store/auth-store";
function isLoopbackHost(hostname) {
    return hostname === "127.0.0.1" || hostname === "localhost" || hostname.endsWith(".localhost");
}
function resolveApiBaseUrl() {
    const currentHostname = globalThis.location?.hostname ?? "";
    const currentOrigin = globalThis.location?.origin ?? "";
    const runtimeValue = globalThis.__GETUPSOFT_API_BASE_URL__;
    if (runtimeValue) {
        try {
            const runtimeUrl = new URL(runtimeValue, currentOrigin || undefined);
            if (!isLoopbackHost(currentHostname) && isLoopbackHost(runtimeUrl.hostname)) {
                return currentOrigin;
            }
        }
        catch {
            // Ignore malformed runtime values and keep fallback chain.
        }
        return runtimeValue;
    }
    const envValue = import.meta.env.VITE_API_BASE_URL;
    if (envValue) {
        return envValue;
    }
    if (currentOrigin && (currentHostname === "getupsoft.com.do" || currentHostname.endsWith(".getupsoft.com.do") || isLoopbackHost(currentHostname))) {
        return currentOrigin;
    }
    return "http://localhost:8000";
}
export const api = createApiClient({
    baseURL: resolveApiBaseUrl(),
    getAccessToken: () => useAuthStore.getState().accessToken,
    onUnauthorized: () => useAuthStore.getState().clearSession(),
});
api.interceptors.request.use((config) => {
    config.baseURL = resolveApiBaseUrl();
    return config;
});
