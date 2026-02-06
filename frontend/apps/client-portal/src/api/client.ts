import { createApiClient } from "@getupsoft/api-client";
import { useAuthStore } from "../store/auth-store";

export const api = createApiClient({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  getAccessToken: () => useAuthStore.getState().accessToken,
  getTenantId: () => useAuthStore.getState().user?.tenantId ?? undefined,
  onUnauthorized: () => useAuthStore.getState().clearSession(),
});
