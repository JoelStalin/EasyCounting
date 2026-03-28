import { create } from "zustand";
const STORAGE_KEY = "getupsoft-app-auth";
function readSession() {
    if (typeof window === "undefined") {
        return null;
    }
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) {
        return null;
    }
    try {
        return JSON.parse(raw);
    }
    catch (error) {
        console.warn("No se pudo parsear la sesión almacenada", error);
        return null;
    }
}
function persistSession(session) {
    if (typeof window === "undefined") {
        return;
    }
    if (session) {
        window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    }
    else {
        window.sessionStorage.removeItem(STORAGE_KEY);
    }
}
export const useAuthStore = create((set) => ({
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
