import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { api } from "../api/client";
import { useAuth } from "../auth/use-auth";
export function MFAPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { setSession } = useAuth();
    const [code, setCode] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const email = location.state?.email;
    useEffect(() => {
        if (!email) {
            navigate("/login", { replace: true });
        }
    }, [email, navigate]);
    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const { data } = await api.post("/auth/mfa/verify", {
                email,
                code,
            });
            setSession({
                accessToken: data.accessToken,
                refreshToken: data.refreshToken,
                user: data.user,
                permissions: data.permissions,
            });
            navigate("/dashboard", { replace: true });
        }
        catch (err) {
            setError("Código inválido o expirado.");
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsx("div", { className: "flex min-h-screen items-center justify-center bg-slate-950 px-4", children: _jsxs(Card, { className: "w-full max-w-md", children: [_jsxs(CardHeader, { className: "space-y-2 text-center", children: [_jsx(CardTitle, { children: "Verificaci\u00F3n MFA" }), _jsx("p", { className: "text-sm text-slate-300", children: "Confirma tu identidad para emitir e-CF y RFCE." })] }), _jsx(CardContent, { children: _jsxs("form", { className: "space-y-6", onSubmit: handleSubmit, children: [_jsx("div", { className: "space-y-4", children: _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "mfa-code", children: "C\u00F3digo" }), _jsx(Input, { id: "mfa-code", type: "text", inputMode: "numeric", pattern: "[0-9]{6}", maxLength: 6, className: "text-center text-lg tracking-[0.35em]", value: code, onChange: (event) => setCode(event.target.value), required: true })] }) }), _jsx(Button, { className: "w-full", type: "submit", disabled: loading, children: loading ? _jsx(Spinner, { label: "Verificando" }) : "Confirmar" }), error ? _jsx("p", { className: "text-center text-sm text-red-400", children: error }) : null] }) })] }) }));
}
