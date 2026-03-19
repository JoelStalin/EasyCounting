import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function DataTable({ data, columns, emptyMessage = "Sin registros" }) {
    if (data.length === 0) {
        return (_jsx("div", { className: "rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-sm text-slate-300", children: emptyMessage }));
    }
    return (_jsx("div", { className: "overflow-hidden rounded-xl border border-slate-800", children: _jsxs("table", { className: "min-w-full divide-y divide-slate-800", children: [_jsx("thead", { className: "bg-slate-900/80 text-left text-xs uppercase tracking-wide text-slate-400", children: _jsx("tr", { children: columns.map((column) => (_jsx("th", { className: "px-4 py-3", children: column.header }, column.header))) }) }), _jsx("tbody", { className: "divide-y divide-slate-800 bg-slate-950/40", children: data.map((row, index) => (_jsx("tr", { className: "text-sm text-slate-200", children: columns.map((column) => (_jsx("td", { className: "px-4 py-3 align-top", children: column.cell(row) }, column.header))) }, index))) })] }) }));
}
