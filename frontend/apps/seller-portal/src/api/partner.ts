import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export interface PartnerProfile {
  accountId: number;
  accountName: string;
  accountSlug: string;
  userEmail: string;
  role: string;
  scope: "PARTNER";
}

export interface PartnerTenantItem {
  id: number;
  name: string;
  rnc: string;
  env: string;
  status: string;
  canEmit: boolean;
  canManage: boolean;
  invoiceCount: number;
  totalAmount: string;
}

export interface PartnerDashboardResponse {
  partner: PartnerProfile;
  tenantCount: number;
  invoiceCount: number;
  acceptedCount: number;
  pendingCount: number;
  totalAmount: string;
  tenants: PartnerTenantItem[];
}

export interface PartnerInvoiceItem {
  id: number;
  tenantId: number;
  tenantName: string;
  encf: string;
  tipoEcf: string;
  estadoDgii: string;
  trackId: string | null;
  total: string;
  fechaEmision: string;
}

export interface PartnerInvoiceListResponse {
  items: PartnerInvoiceItem[];
  total: number;
  page: number;
  size: number;
}

export interface PartnerEmitPayload {
  tenantId: number;
  encf: string;
  tipoEcf: string;
  rncReceptor?: string;
  total: string;
}

export interface PartnerEmitResponse {
  invoiceId: number;
  tenantId: number;
  encf: string;
  estadoDgii: string;
  trackId: string;
  total: string;
  message: string;
}

export function usePartnerProfile(enabled = true) {
  return useQuery({
    queryKey: ["partner", "me"],
    enabled,
    queryFn: async () => {
      const { data } = await api.get<PartnerProfile>("/api/v1/partner/me");
      return data;
    },
  });
}

export function usePartnerDashboard() {
  return useQuery({
    queryKey: ["partner", "dashboard"],
    queryFn: async () => {
      const { data } = await api.get<PartnerDashboardResponse>("/api/v1/partner/dashboard");
      return data;
    },
  });
}

export function usePartnerTenants() {
  return useQuery({
    queryKey: ["partner", "tenants"],
    queryFn: async () => {
      const { data } = await api.get<PartnerTenantItem[]>("/api/v1/partner/tenants");
      return data;
    },
  });
}

export function usePartnerInvoices(params: { tenantId?: number | null; page?: number; size?: number } = {}) {
  const page = params.page ?? 1;
  const size = params.size ?? 20;
  return useQuery({
    queryKey: ["partner", "invoices", params.tenantId ?? null, page, size],
    queryFn: async () => {
      const { data } = await api.get<PartnerInvoiceListResponse>("/api/v1/partner/invoices", {
        params: {
          page,
          size,
          tenant_id: params.tenantId ?? undefined,
        },
      });
      return data;
    },
  });
}

export function useEmitPartnerInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PartnerEmitPayload) => {
      const { data } = await api.post<PartnerEmitResponse>("/api/v1/partner/emit", payload);
      return data;
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["partner", "dashboard"] }),
        queryClient.invalidateQueries({ queryKey: ["partner", "tenants"] }),
        queryClient.invalidateQueries({ queryKey: ["partner", "invoices"] }),
      ]);
    },
  });
}
