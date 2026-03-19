import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export interface Plan {
  id: number;
  name: string;
  precio_mensual: string;
  precio_por_documento: string;
  documentos_incluidos: number;
  max_facturas_mes: number;
  max_facturas_por_receptor_mes: number;
  max_monto_por_factura: string;
  descripcion: string | null;
  created_at: string;
  updated_at: string;
}

export interface TenantPlanSummary {
  tenant_id: number;
  current_plan: Plan | null;
  pending_plan: Plan | null;
  pending_effective_at: string | null;
  pending_requested_at: string | null;
}

export function usePlans() {
  return useQuery({
    queryKey: ["tenant", "plans"],
    queryFn: async () => {
      const { data } = await api.get<Plan[]>("/api/v1/cliente/plans");
      return data;
    },
  });
}

export function useTenantPlan() {
  return useQuery({
    queryKey: ["tenant", "plan"],
    queryFn: async () => {
      const { data } = await api.get<TenantPlanSummary>("/api/v1/cliente/plan");
      return data;
    },
  });
}

export function useRequestPlanChange() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (planId: number) => {
      const { data } = await api.put<TenantPlanSummary>("/api/v1/cliente/plan", {
        plan_id: planId,
      });
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "plan"] });
      await queryClient.invalidateQueries({ queryKey: ["tenant", "usage"] });
    },
  });
}
