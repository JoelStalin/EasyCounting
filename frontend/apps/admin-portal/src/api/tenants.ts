import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

interface TenantPlanResponse {
  tenant_id: number;
  plan: {
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
  } | null;
}

export interface TenantItem {
  id: number;
  name: string;
  rnc: string;
  env: string;
  status: string;
}

export interface TenantCreatePayload {
  name: string;
  rnc: string;
  env?: string;
  dgii_base_ecf?: string | null;
  dgii_base_fc?: string | null;
}

export interface TenantUpdatePayload {
  name?: string;
  rnc?: string;
  env?: string;
}

export function useTenants() {
  return useQuery({
    queryKey: ["admin", "tenants"],
    queryFn: async () => {
      const { data } = await api.get<TenantItem[]>("/api/v1/admin/tenants");
      return data;
    },
  });
}

export function useTenant(tenantId?: string) {
  return useQuery({
    queryKey: ["admin", "tenant", tenantId],
    enabled: Boolean(tenantId),
    queryFn: async () => {
      const { data } = await api.get<TenantItem>(`/api/v1/admin/tenants/${tenantId}`);
      return data;
    },
  });
}

export function useCreateTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantCreatePayload) => {
      const { data } = await api.post<TenantItem>("/api/v1/admin/tenants", payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "tenants"] });
    },
  });
}

export function useUpdateTenant(tenantId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantUpdatePayload) => {
      const { data } = await api.put<TenantItem>(`/api/v1/admin/tenants/${tenantId}`, payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "tenant", tenantId] });
      await queryClient.invalidateQueries({ queryKey: ["admin", "tenants"] });
    },
  });
}

export function useTenantPlan(tenantId?: string) {
  return useQuery({
    queryKey: ["admin", "tenant-plan", tenantId],
    enabled: Boolean(tenantId),
    queryFn: async () => {
      const { data } = await api.get<TenantPlanResponse>(`/api/v1/admin/tenants/${tenantId}/plan`);
      return data;
    },
  });
}

export function useAssignTenantPlan(tenantId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (planId: number | null) => {
      const { data } = await api.put<TenantPlanResponse>(`/api/v1/admin/tenants/${tenantId}/plan`, {
        plan_id: planId,
      });
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "tenant-plan", tenantId] });
    },
  });
}
