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

export interface PlanCreatePayload {
  name: string;
  precio_mensual: string;
  precio_por_documento: string;
  documentos_incluidos: number;
  max_facturas_mes: number;
  max_facturas_por_receptor_mes: number;
  max_monto_por_factura: string;
  descripcion: string | null;
}

export interface PlanUpdatePayload {
  name?: string;
  precio_mensual?: string;
  precio_por_documento?: string;
  documentos_incluidos?: number;
  max_facturas_mes?: number;
  max_facturas_por_receptor_mes?: number;
  max_monto_por_factura?: string;
  descripcion?: string | null;
}

export function usePlans() {
  return useQuery({
    queryKey: ["admin", "plans"],
    queryFn: async () => {
      const { data } = await api.get<Plan[]>("/api/v1/admin/plans");
      return data;
    },
  });
}

export function useCreatePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PlanCreatePayload) => {
      const { data } = await api.post<Plan>("/api/v1/admin/plans", payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
    },
  });
}

export function useUpdatePlan(planId?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PlanUpdatePayload) => {
      const { data } = await api.put<Plan>(`/api/v1/admin/plans/${planId}`, payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
    },
  });
}

export function useDeletePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (planId: number) => {
      await api.delete(`/api/v1/admin/plans/${planId}`);
      return planId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "plans"] });
    },
  });
}
