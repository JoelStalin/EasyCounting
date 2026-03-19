interface StatusBadgeProps {
  status: "ACEPTADO" | "EN_PROCESO" | "RECHAZADO" | string;
}

const COLORS: Record<string, string> = {
  ACEPTADO: "bg-emerald-500/20 text-emerald-200",
  EN_PROCESO: "bg-amber-500/20 text-amber-200",
  RECHAZADO: "bg-red-500/20 text-red-200",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const color = COLORS[status] ?? "bg-slate-500/20 text-slate-200";
  return <span className={`rounded-full px-3 py-1 text-xs font-medium ${color}`}>{status}</span>;
}
