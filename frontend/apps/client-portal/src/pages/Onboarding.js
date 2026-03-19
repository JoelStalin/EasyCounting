import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { useCompleteOnboardingMutation, useOnboardingQuery } from "../api/onboarding";
import { useAuth } from "../auth/use-auth";
export function OnboardingPage() {
    const navigate = useNavigate();
    const { accessToken, refreshToken, permissions, setSession, user } = useAuth();
    const onboardingQuery = useOnboardingQuery(Boolean(user));
    const completeMutation = useCompleteOnboardingMutation();
    const [companyName, setCompanyName] = useState("");
    const [rnc, setRnc] = useState("");
    const [contactEmail, setContactEmail] = useState("");
    const [contactPhone, setContactPhone] = useState("");
    const [notes, setNotes] = useState("");
    useEffect(() => {
        if (!onboardingQuery.data) {
            return;
        }
        setCompanyName(onboardingQuery.data.companyName);
        setRnc(onboardingQuery.data.rnc);
        setContactEmail(onboardingQuery.data.contactEmail ?? "");
        setContactPhone(onboardingQuery.data.contactPhone ?? "");
        setNotes(onboardingQuery.data.notes ?? "");
    }, [onboardingQuery.data]);
    const handleSubmit = async (event) => {
        event.preventDefault();
        const updated = await completeMutation.mutateAsync({
            companyName,
            rnc,
            contactEmail,
            contactPhone,
            notes,
        });
        if (accessToken && refreshToken && user) {
            setSession({
                accessToken,
                refreshToken,
                permissions,
                user: {
                    ...user,
                    onboardingStatus: updated.onboardingStatus,
                },
            });
        }
        navigate("/dashboard", { replace: true });
    };
    return (_jsxs("div", { className: "space-y-6", "data-tour": "client-onboarding", children: [_jsxs("header", { className: "space-y-1", children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Configura tu emisor" }), _jsx("p", { className: "text-sm text-slate-300", children: "Completa estos datos antes de habilitar operaciones fiscales reales y certificados." })] }), _jsxs(Card, { children: [_jsx(CardHeader, { children: _jsx(CardTitle, { children: "Onboarding fiscal" }) }), _jsx(CardContent, { children: onboardingQuery.isLoading ? (_jsx(Spinner, { label: "Cargando onboarding" })) : (_jsxs("form", { className: "grid gap-4 md:grid-cols-2", onSubmit: handleSubmit, children: [_jsxs("div", { className: "space-y-2 md:col-span-2", children: [_jsx(Label, { htmlFor: "company-name", children: "Nombre comercial" }), _jsx(Input, { id: "company-name", value: companyName, onChange: (event) => setCompanyName(event.target.value), required: true })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "company-rnc", children: "RNC" }), _jsx(Input, { id: "company-rnc", value: rnc, onChange: (event) => setRnc(event.target.value), required: true })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "contact-email", children: "Correo fiscal" }), _jsx(Input, { id: "contact-email", value: contactEmail, onChange: (event) => setContactEmail(event.target.value) })] }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "contact-phone", children: "Telefono" }), _jsx(Input, { id: "contact-phone", value: contactPhone, onChange: (event) => setContactPhone(event.target.value) })] }), _jsxs("div", { className: "space-y-2 md:col-span-2", children: [_jsx(Label, { htmlFor: "notes", children: "Notas" }), _jsx("textarea", { id: "notes", className: "min-h-28 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100", value: notes, onChange: (event) => setNotes(event.target.value) })] }), _jsx("div", { className: "md:col-span-2 flex justify-end", children: _jsx(Button, { type: "submit", disabled: completeMutation.isPending, children: completeMutation.isPending ? _jsx(Spinner, { label: "Guardando" }) : "Completar onboarding" }) })] })) })] })] }));
}
