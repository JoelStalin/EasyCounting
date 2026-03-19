import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, Spinner } from "@getupsoft/ui";
import { exchangeSocialTicket } from "../api/auth";
import { useAuth } from "../auth/use-auth";
export function AuthCallbackPage() {
    const navigate = useNavigate();
    const [params] = useSearchParams();
    const { setSession } = useAuth();
    useEffect(() => {
        const ticket = params.get("ticket");
        if (!ticket) {
            navigate("/login", { replace: true });
            return;
        }
        exchangeSocialTicket(ticket)
            .then((response) => {
            if ("mfaRequired" in response) {
                navigate("/mfa", {
                    replace: true,
                    state: { challengeId: response.challengeId, returnTo: response.returnTo ?? "/dashboard" },
                });
                return;
            }
            setSession({
                accessToken: response.accessToken,
                refreshToken: response.refreshToken,
                user: response.user,
                permissions: response.permissions,
            });
            navigate(response.returnTo ?? "/dashboard", { replace: true });
        })
            .catch(() => {
            navigate("/login", { replace: true });
        });
    }, [navigate, params, setSession]);
    return (_jsx("div", { className: "flex min-h-screen items-center justify-center bg-slate-950 px-4", children: _jsxs(Card, { className: "w-full max-w-md", children: [_jsx(CardHeader, { className: "space-y-2 text-center", children: _jsx(CardTitle, { children: "Conectando tu cuenta" }) }), _jsx(CardContent, { className: "flex justify-center", children: _jsx(Spinner, { label: "Procesando acceso social" }) })] }) }));
}
