import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface DashboardKpis {
  month: string;
  generated_at: string;
  companies_active: number;
  invoices_month: number;
  invoices_accepted: number;
  invoices_rejected: number;
  invoices_other: number;
  amount_due_month: string;
}

export interface AdminInvoiceListItem {
  id: number;
  tenant_id: number;
  tenant_name: string;
  encf: string;
  tipo_ecf: string;
  estado_dgii: string;
  track_id: string | null;
  total: string;
  fecha_emision: string;
}

export interface AdminInvoiceListResponse {
  items: AdminInvoiceListItem[];
  total: number;
  page: number;
  size: number;
}

export function useDashboardKpis(month?: string) {
  return useQuery({
    queryKey: ["admin", "dashboard", "kpis", month],
    queryFn: async () => {
      const { data } = await api.get<DashboardKpis>("/api/v1/admin/dashboard/kpis", {
        params: month ? { month } : undefined,
      });
      return data;
    },
  });
}

export function useAdminInvoices(params?: {
  page?: number;
  size?: number;
  tenantId?: number;
  estado?: string;
  tipoEcf?: string;
  encf?: string;
  trackId?: string;
  dateFrom?: string;
  dateTo?: string;
}) {
  return useQuery({
    queryKey: ["admin", "invoices", params],
    queryFn: async () => {
      const { data } = await api.get<AdminInvoiceListResponse>("/api/v1/admin/invoices", {
        params: {
          page: params?.page ?? 1,
          size: params?.size ?? 20,
          tenant_id: params?.tenantId,
          estado_dgii: params?.estado,
          tipo_ecf: params?.tipoEcf,
          encf: params?.encf,
          track_id: params?.trackId,
          date_from: params?.dateFrom,
          date_to: params?.dateTo,
        },
      });
      return data;
    },
  });
}
