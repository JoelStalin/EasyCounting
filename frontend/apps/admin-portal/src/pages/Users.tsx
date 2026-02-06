import { DataTable } from "../components/DataTable";
import { type PlatformUserItem, usePlatformUsers } from "../api/platform-users";

interface PlatformUser {
  id: number;
  email: string;
  role: string;
  scope: string;
}

export function PlatformUsersPage() {
  const usersQuery = usePlatformUsers();
  const rows: PlatformUser[] = (usersQuery.data ?? []).map((user: PlatformUserItem) => ({
    id: user.id,
    email: user.email,
    role: user.role,
    scope: user.scope,
  }));

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Usuarios plataforma</h1>
          <p className="text-sm text-slate-300">Controla roles y permisos globales del ecosistema.</p>
        </div>
        <button className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90">
          Invitar usuario
        </button>
      </header>
      {usersQuery.isError ? (
        <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-200">
          No se pudo cargar el listado de usuarios.
        </div>
      ) : null}
      <DataTable
        data={rows}
        columns={[
          { header: "Correo", cell: (row) => <span className="text-sm text-slate-200">{row.email}</span> },
          { header: "Rol", cell: (row) => <span className="text-sm text-slate-300">{row.role}</span> },
          { header: "Scope", cell: (row) => <span className="text-sm text-slate-300">{row.scope}</span> },
        ]}
        emptyMessage={usersQuery.isLoading ? "Cargando usuarios…" : usersQuery.isError ? "Error cargando usuarios" : "Sin usuarios"}
      />
    </div>
  );
}
