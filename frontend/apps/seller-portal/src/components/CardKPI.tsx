import { ReactNode } from "react";

interface CardKPIProps {
  title: string;
  value: string;
  subtitle?: string;
  icon?: ReactNode;
}

export function CardKPI({ title, value, subtitle, icon }: CardKPIProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
      <div className="flex items-center justify-between text-sm text-slate-300">
        <span>{title}</span>
        {icon ?? null}
      </div>
      <span className="text-2xl font-semibold text-white">{value}</span>
      {subtitle ? <span className="text-xs text-slate-400">{subtitle}</span> : null}
    </div>
  );
}
