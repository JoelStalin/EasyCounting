import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from "react";
import { GuidedTour } from "@getupsoft/ui";
import { useLocation } from "react-router-dom";
import { useMyToursQuery, useUpsertTourMutation } from "../api/ui-tours";
import { useAuth } from "../auth/use-auth";
import { CLIENT_TOURS } from "./catalog";
function patternToRegex(pattern) {
    return new RegExp(`^${pattern.replace(/:[^/]+/g, "[^/]+")}$`);
}
function resolveDefinition(pathname) {
    return CLIENT_TOURS.find((tour) => tour.patterns.some((pattern) => patternToRegex(pattern).test(pathname))) ?? null;
}
export function TourController() {
    const location = useLocation();
    const { isAuthenticated } = useAuth();
    const toursQuery = useMyToursQuery(isAuthenticated);
    const upsertMutation = useUpsertTourMutation();
    const definition = useMemo(() => resolveDefinition(location.pathname), [location.pathname]);
    const [run, setRun] = useState(false);
    const persisted = useMemo(() => {
        if (!definition || !toursQuery.data) {
            return null;
        }
        return toursQuery.data.find((item) => item.viewKey === definition.viewKey) ?? null;
    }, [definition, toursQuery.data]);
    useEffect(() => {
        if (!definition || !isAuthenticated || toursQuery.isLoading) {
            return;
        }
        if (!persisted || persisted.tourVersion < definition.version || persisted.status === "pending") {
            setRun(true);
            return;
        }
        setRun(false);
    }, [definition, isAuthenticated, persisted, toursQuery.isLoading]);
    if (!definition) {
        return null;
    }
    return (_jsxs(_Fragment, { children: [_jsx("button", { type: "button", "data-tour": "tour-trigger", className: "rounded-md border border-slate-700 px-4 py-2 text-xs font-semibold text-slate-200 hover:border-primary hover:text-primary", onClick: () => setRun(true), children: "Ver tour" }), _jsx(GuidedTour, { run: run, steps: definition.steps, onFinished: (status, lastStep) => {
                    setRun(false);
                    upsertMutation.mutate({
                        viewKey: definition.viewKey,
                        tourVersion: definition.version,
                        status,
                        lastStep,
                    });
                } })] }));
}
