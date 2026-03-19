import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { startSocialLogin, useLoginMutation, useSocialProvidersQuery } from "../api/auth";
import { useAuth } from "../auth/use-auth";
const DEMO_ACCOUNTS = [
    {
        title: "Revendedor demo",
        email: "seller@getupsoft.com.do",
        password: "Seller123!",
        note: "Puede ver clientes asignados y emitir demo solo en su cartera.",
    },
    {
        title: "Auditor demo",
        email: "seller.auditor@getupsoft.com.do",
        password: "SellerAudit123!",
        note: "Mismo alcance de cartera, pero sin permiso de emision.",
    },
];
export function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const navigate = useNavigate();
    const location = useLocation();
    const { mutateAsync, isPending, isError } = useLoginMutation();
    const { isAuthenticated } = useAuth();
    const providersQuery = useSocialProvidersQuery();
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
            navigate("/mfa", { state: { challengeId: response.challenge_id, returnTo: from } });
            return;
        }
        navigate(from, { replace: true });
    };
    return (_jsxs("div", { className: "grid min-h-screen gap-6 bg-slate-950 px-4 py-10 xl:grid-cols-[1.1fr,0.9fr]", children: [_jsx("div", { className: "flex items-center justify-center", children: _jsxs(Card, { className: "w-full max-w-md", children: [_jsxs(CardHeader, { className: "space-y-2 text-center", children: [_jsx(CardTitle, { children: "getupsoft Socios" }), _jsx("p", { className: "text-sm text-slate-300", children: "Portal para revendedores y operadores con acceso restringido a sus clientes." })] }), _jsx(CardContent, { children: _jsxs("form", { className: "space-y-6", onSubmit: handleSubmit, children: [_jsxs("div", { className: "space-y-4", children: [_jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "email", children: "Correo electronico" }), _jsx(Input, { "data-tour": "login-email", id: "email", type: "email", autoComplete: "email", value: email, onChange: (event) => setEmail(event.target.value), required: true })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "password", children: "Contrasena" }), _jsx(Input, { "data-tour": "login-password", id: "password", type: "password", autoComplete: "current-password", value: password, onChange: (event) => setPassword(event.target.value), required: true })] })] }), _jsx(Button, { className: "w-full", type: "submit", disabled: isPending, "data-tour": "login-submit", children: isPending ? _jsx(Spinner, { label: "Validando" }) : "Ingresar" }), providersQuery.data && providersQuery.data.length > 0 ? (_jsx("div", { className: "space-y-2 border-t border-slate-800 pt-4", "data-tour": "login-social", children: providersQuery.data.map((provider) => (_jsxs("button", { type: "button", className: "w-full rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-primary hover:text-primary", onClick: () => startSocialLogin(provider.provider, from), children: ["Continuar con ", provider.label] }, provider.provider))) })) : null, isError ? (_jsx("p", { className: "text-center text-sm text-red-400", children: "Credenciales invalidas o cuenta sin perfil seller." })) : null] }) })] }) }), _jsx("div", { className: "flex items-center justify-center", children: _jsxs(Card, { className: "w-full max-w-xl", children: [_jsxs(CardHeader, { className: "space-y-2", children: [_jsx(CardTitle, { children: "Modo demo para partners" }), _jsx("p", { className: "text-sm text-slate-300", children: "Estas credenciales dummy sirven para prospectos y validaciones no fiscales." })] }), _jsxs(CardContent, { className: "space-y-4", children: [DEMO_ACCOUNTS.map((account) => (_jsxs("div", { className: "rounded-xl border border-slate-800 bg-slate-900/50 p-4", children: [_jsx("p", { className: "font-medium text-slate-100", children: account.title }), _jsx("p", { className: "mt-1 text-xs text-slate-400", children: account.note }), _jsxs("button", { type: "button", className: "mt-3 w-full rounded-md border border-slate-700 px-3 py-2 text-left text-sm text-slate-200 hover:border-primary hover:text-primary", onClick: () => {
                                                setEmail(account.email);
                                                setPassword(account.password);
                                            }, children: [account.email, _jsx("span", { className: "block font-mono text-xs text-slate-400", children: account.password })] })] }, account.email))), _jsx("div", { className: "rounded-xl border border-amber-900/60 bg-amber-950/30 p-4 text-sm text-amber-100", children: "El acceso demo esta aislado del entorno principal y opera con datos ficticios de clientes y comprobantes." })] })] }) })] }));
}
