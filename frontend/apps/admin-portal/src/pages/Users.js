import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { DataTable } from "../components/DataTable";
import { usePlatformUsers } from "../api/platform-users";
export function PlatformUsersPage() {
    const usersQuery = usePlatformUsers();
    const rows = (usersQuery.data ?? []).map((user) => ({
        id: user.id,
        email: user.email,
        role: user.role,
        scope: user.scope,
    }));
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("header", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-semibold text-white", children: "Usuarios plataforma" }), _jsx("p", { className: "text-sm text-slate-300", children: "Controla roles y permisos globales del ecosistema." })] }), _jsx("button", { className: "rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90", children: "Invitar usuario" })] }), usersQuery.isError ? (_jsx("div", { className: "rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200", children: "No se pudo cargar el listado de usuarios." })) : null, _jsx(DataTable, { data: rows, columns: [
                    { header: "Correo", cell: (row) => _jsx("span", { className: "text-sm text-slate-200", children: row.email }) },
                    { header: "Rol", cell: (row) => _jsx("span", { className: "text-sm text-slate-300", children: row.role }) },
                    { header: "Scope", cell: (row) => _jsx("span", { className: "text-sm text-slate-300", children: row.scope }) },
                ], emptyMessage: usersQuery.isLoading ? "Cargando usuarios…" : usersQuery.isError ? "Error cargando usuarios" : "Sin usuarios" })] }));
}
