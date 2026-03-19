import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function CardKPI({ title, value, subtitle, icon }) {
    return (_jsxs("div", { className: "flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4", children: [_jsxs("div", { className: "flex items-center justify-between text-sm text-slate-300", children: [_jsx("span", { children: title }), icon ?? null] }), _jsx("span", { className: "text-2xl font-semibold text-white", children: value }), subtitle ? _jsx("span", { className: "text-xs text-slate-400", children: subtitle }) : null] }));
}
