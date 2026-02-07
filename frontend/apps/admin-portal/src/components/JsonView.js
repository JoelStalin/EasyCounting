import { jsx as _jsx } from "react/jsx-runtime";
export function JsonView({ data }) {
    return (_jsx("pre", { className: "max-h-72 overflow-auto rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-xs text-slate-200", children: JSON.stringify(data, null, 2) }));
}
