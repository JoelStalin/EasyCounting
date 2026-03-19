import { ShieldAlert } from "lucide-react";

interface ForbiddenStateProps {
  title?: string;
  description?: string;
}

export function ForbiddenState({
  title = "Acceso restringido",
  description = "Solicita permisos a tu administrador para continuar.",
}: ForbiddenStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center">
      <ShieldAlert className="h-10 w-10 text-primary" aria-hidden />
      <div className="space-y-1">
        <h2 className="text-xl font-semibold text-white">{title}</h2>
        <p className="text-sm text-slate-300">{description}</p>
      </div>
    </div>
  );
}
