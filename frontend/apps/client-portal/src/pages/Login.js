import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { useLoginMutation } from "../api/auth";
import { useAuth } from "../auth/use-auth";
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
    return (_jsx("div", { className: "flex min-h-screen items-center justify-center bg-slate-950 px-4", children: _jsxs(Card, { className: "w-full max-w-md", children: [_jsxs(CardHeader, { className: "space-y-2 text-center", children: [_jsx(CardTitle, { children: "getupsoft Cliente" }), _jsx("p", { className: "text-sm text-slate-300", children: "Portal para emisi\u00F3n y seguimiento de comprobantes electr\u00F3nicos." })] }), _jsx(CardContent, { children: _jsxs("form", { className: "space-y-6", onSubmit: handleSubmit, children: [_jsxs("div", { className: "space-y-4", children: [_jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "email", children: "Correo electr\u00F3nico" }), _jsx(Input, { id: "email", type: "email", autoComplete: "email", value: email, onChange: (event) => setEmail(event.target.value), required: true })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "password", children: "Contrase\u00F1a" }), _jsx(Input, { id: "password", type: "password", autoComplete: "current-password", value: password, onChange: (event) => setPassword(event.target.value), required: true })] })] }), _jsx(Button, { className: "w-full", type: "submit", disabled: isPending, children: isPending ? _jsx(Spinner, { label: "Validando" }) : "Ingresar" }), isError ? _jsx("p", { className: "text-center text-sm text-red-400", children: "Credenciales inv\u00E1lidas o MFA requerido." }) : null] }) })] }) }));
}
