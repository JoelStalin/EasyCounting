import { jsx as _jsx, Fragment as _Fragment } from "react/jsx-runtime";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./use-auth";
import { ForbiddenState } from "../components/ForbiddenState";
import { Spinner } from "../components/Spinner";
export function RequireAuth({ children }) {
    const { isAuthenticated, loading } = useAuth();
    const location = useLocation();
    if (loading) {
        return (_jsx("div", { className: "flex h-full items-center justify-center", children: _jsx(Spinner, { label: "Verificando sesi\u00F3n" }) }));
    }
    if (!isAuthenticated) {
        return _jsx(Navigate, { to: "/login", replace: true, state: { from: location } });
    }
    return _jsx(_Fragment, { children: children });
}
export function RequirePermission({ anyOf, children }) {
    const { hasAnyPermission, loading } = useAuth();
    if (loading) {
        return (_jsx("div", { className: "flex h-full items-center justify-center", children: _jsx(Spinner, { label: "Verificando permisos" }) }));
    }
    if (!hasAnyPermission(anyOf)) {
        return _jsx(ForbiddenState, {});
    }
    return _jsx(_Fragment, { children: children });
}
export function RequireScope({ scope, children }) {
    const { scope: currentScope, loading } = useAuth();
    if (loading) {
        return (_jsx("div", { className: "flex h-full items-center justify-center", children: _jsx(Spinner, { label: "Cargando" }) }));
    }
    if (currentScope !== scope) {
        return _jsx(ForbiddenState, { description: "Esta secci\u00F3n pertenece a otro tipo de cuenta." });
    }
    return _jsx(_Fragment, { children: children });
}
export function RequireMFA({ children, mfaCompleted }) {
    if (!mfaCompleted) {
        return _jsx(ForbiddenState, { description: "Completa MFA para emitir comprobantes." });
    }
    return _jsx(_Fragment, { children: children });
}
