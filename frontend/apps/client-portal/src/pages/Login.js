import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { useLoginMutation } from "../api/auth";
import { useAuth } from "../auth/use-auth";
const DEMO_ACCOUNTS = [
    {
        title: "Cliente demo",
        email: "cliente@getupsoft.com.do",
        password: "Tenant123!",
        note: "Acceso de prospecto para revisar dashboard, emisiÃ³n simulada y perfil.",
    },
    {
        title: "Operador demo",
        email: "cliente.operador@getupsoft.com.do",
        password: "TenantOps123!",
        note: "Cuenta adicional para validaciones internas y pruebas funcionales.",
    },
];
export function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();
    const location = useLocation();
    const { mutateAsync, isPending, isError } = useLoginMutation();
    const { isAuthenticated } = useAuth();
    const from = useMemo(() => {
        const state = location.state;
        return state?.from?.pathname ?? "/dashboard";
    }, [location.state]);
    useEffect(() => {
        if (isAuthenticated) {
            navigate(from, { replace: true });
        }
    }, [from, isAuthenticated, navigate]);
    const handleSubmit = async (event) => {
        event.preventDefault();
        const response = await mutateAsync({ email, password });
        if (response.mfa_required) {
            navigate("/mfa", { state: { email } });
            return;
        }
        navigate(from, { replace: true });
    };
    return (_jsxs("div", { className: "grid min-h-screen gap-6 bg-slate-950 px-4 py-10 xl:grid-cols-[1.05fr,0.95fr]", children: [_jsx("div", { className: "flex items-center justify-center", children: _jsxs(Card, { className: "w-full max-w-md", children: [_jsxs(CardHeader, { className: "space-y-2 text-center", children: [_jsx(CardTitle, { children: "getupsoft Cliente" }), _jsx("p", { className: "text-sm text-slate-300", children: "Portal para emisi\u00C3\u00B3n y seguimiento de comprobantes electr\u00C3\u00B3nicos." })] }), _jsx(CardContent, { children: _jsxs("form", { className: "space-y-6", onSubmit: handleSubmit, children: [_jsxs("div", { className: "space-y-4", children: [_jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "email", children: "Correo electr\u00C3\u00B3nico" }), _jsx(Input, { id: "email", type: "email", autoComplete: "email", value: email, onChange: (event) => setEmail(event.target.value), required: true })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "password", children: "Contrase\u00C3\u00B1a" }), _jsx(Input, { id: "password", type: "password", autoComplete: "current-password", value: password, onChange: (event) => setPassword(event.target.value), required: true })] })] }), _jsx(Button, { className: "w-full", type: "submit", disabled: isPending, children: isPending ? _jsx(Spinner, { label: "Validando" }) : "Ingresar" }), isError ? _jsx("p", { className: "text-center text-sm text-red-400", children: "Credenciales inv\u00C3\u00A1lidas o MFA requerido." }) : null] }) })] }) }), _jsx("div", { className: "flex items-center justify-center", children: _jsxs(Card, { className: "w-full max-w-xl", children: [_jsxs(CardHeader, { className: "space-y-2", children: [_jsx(CardTitle, { children: "Modo demo para clientes" }), _jsx("p", { className: "text-sm text-slate-300", children: "Credenciales dummy para demos comerciales y recorridos guiados del producto." })] }), _jsxs(CardContent, { className: "space-y-4", children: [DEMO_ACCOUNTS.map((account) => (_jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-900/50 p-4", children: [_jsx("p", { className: "font-medium text-slate-100", children: account.title }), _jsx("p", { className: "mt-1 text-xs text-slate-400", children: account.note }), _jsxs("button", { type: "button", className: "mt-3 w-full rounded-md border border-slate-700 px-3 py-2 text-left text-sm text-slate-200 hover:border-primary hover:text-primary", onClick: () => {
                                                setEmail(account.email);
                                                setPassword(account.password);
                                            }, children: [account.email, _jsx("span", { className: "block font-mono text-xs text-slate-400", children: account.password })] })] }, account.email))), _jsx("div", { className: "rounded-xl border border-amber-900/60 bg-amber-950/30 p-4 text-sm text-amber-100", children: "Este entorno demo usa datos ficticios y no emite comprobantes fiscales reales." })] })] }) })] }));
}
