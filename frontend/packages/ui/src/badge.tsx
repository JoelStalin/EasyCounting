import type { HTMLAttributes, ReactElement } from "react";
import { cn } from "./utils";

type BadgeVariant = "default" | "success" | "warning" | "info";

const badgeStyles: Record<BadgeVariant, string> = {
  default: "bg-slate-800 text-slate-100",
  success: "bg-emerald-600/20 text-emerald-300 border border-emerald-500/40",
  warning: "bg-amber-600/20 text-amber-200 border border-amber-500/40",
  info: "bg-sky-600/20 text-sky-200 border border-sky-500/40",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps): ReactElement {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        badgeStyles[variant],
        className,
      )}
      {...props}
    />
  );
}
