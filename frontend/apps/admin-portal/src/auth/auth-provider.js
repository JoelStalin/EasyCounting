import { jsx as _jsx, Fragment as _Fragment } from "react/jsx-runtime";
import { useEffect } from "react";
import { useAuthStore } from "../store/auth-store";
import { Spinner } from "../components/Spinner";
export function AuthProvider({ children }) {
    const hydrate = useAuthStore((state) => state.hydrate);
    const hydrated = useAuthStore((state) => state.hydrated);
    useEffect(() => {
        hydrate();
    }, [hydrate]);
    if (!hydrated) {
        return (_jsx("div", { className: "flex h-screen items-center justify-center", children: _jsx(Spinner, { label: "Inicializando sesi\u00F3n" }) }));
    }
    return _jsx(_Fragment, { children: children });
}
