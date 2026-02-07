import { jsx as _jsx } from "react/jsx-runtime";
export function FileDownloader({ href, label }) {
    return (_jsx("a", { className: "inline-flex items-center justify-center rounded-md border border-slate-700 px-3 py-1 text-xs font-medium text-slate-200 transition hover:border-primary hover:text-primary", href: href, target: "_blank", rel: "noopener noreferrer", children: label }));
}
