import { create } from "zustand";

export type AuthScope = "PLATFORM" | "TENANT";

export interface AuthUser {
  id: string;
  email: string;
  scope: AuthScope;
  tenantId: string | null;
  roles: string[];
}

export interface AuthSession {
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
  permissions: string[];
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  permissions: string[];
  hydrated: boolean;
  hydrate: () => void;
  setSession: (session: AuthSession) => void;
  clearSession: () => void;
}

const STORAGE_KEY = "getupsoft-client-auth";

function readSession(): AuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as AuthSession;
  } catch (error) {
    console.warn("No se pudo parsear la sesión almacenada", error);
    return null;
  }
}

function persistSession(session: AuthSession | null) {
  if (typeof window === "undefined") {
    return;
  }
  if (session) {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } else {
    window.sessionStorage.removeItem(STORAGE_KEY);
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  permissions: [],
  hydrated: false,
  hydrate: () => {
    const session = readSession();
    if (!session) {
      set({ hydrated: true, accessToken: null, refreshToken: null, user: null, permissions: [] });
      return;
    }
    set({
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      user: session.user,
      permissions: session.permissions,
      hydrated: true,
    });
  },
  setSession: (session) => {
    persistSession(session);
    set({
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      user: session.user,
      permissions: session.permissions,
      hydrated: true,
    });
  },
  clearSession: () => {
    persistSession(null);
    set({ accessToken: null, refreshToken: null, user: null, permissions: [], hydrated: true });
  },
}));
