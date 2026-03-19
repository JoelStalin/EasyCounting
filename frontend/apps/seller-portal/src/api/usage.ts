import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface UsageSummary {
  month: string;
  total_used: number;
  included_documents: number;
  remaining_documents: number;
  total_amount: string;
}

export interface UsageInvoiceItem {
  usage_id: number;
  invoice_id: number | null;
  encf: string | null;
  tipo_ecf: string | null;
  estado_dgii: string | null;
  total: string | null;
  monto_cargado: string;
  fecha_emision: string | null;
  fecha_uso: string;
}

export interface UsageListResponse {
  summary: UsageSummary;
  items: UsageInvoiceItem[];
  total: number;
  page: number;
  size: number;
}

export function useUsageSummary(params?: { month?: string; page?: number; size?: number }) {
  return useQuery({
    queryKey: ["tenant", "usage", params],
    queryFn: async () => {
      const { data } = await api.get<UsageListResponse>("/api/v1/cliente/usage", {
        params: {
          month: params?.month,
          page: params?.page,
          size: params?.size,
        },
      });
      return data;
    },
  });
}
