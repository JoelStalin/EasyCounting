import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface InvoiceListItem {
  id: number;
  encf: string;
  tipo_ecf: string;
  estado_dgii: string;
  track_id: string | null;
  total: string;
  fecha_emision: string;
}

export interface InvoiceListResponse {
  items: InvoiceListItem[];
  total: number;
  page: number;
  size: number;
}

export interface InvoiceDetailResponse extends InvoiceListItem {
  xml_path: string;
  xml_hash: string;
  codigo_seguridad: string | null;
  contabilizado: boolean;
  accounted_at: string | null;
  asiento_referencia: string | null;
}

export function useInvoices(params?: { page?: number; size?: number; estado?: string; encf?: string }) {
  return useQuery({
    queryKey: ["tenant", "invoices", params],
    queryFn: async () => {
      const { data } = await api.get<InvoiceListResponse>("/api/v1/cliente/invoices", {
        params: {
          page: params?.page,
          size: params?.size,
          estado_dgii: params?.estado,
          encf: params?.encf,
        },
      });
      return data;
    },
  });
}

export function useInvoiceDetail(invoiceId?: string) {
  return useQuery({
    queryKey: ["tenant", "invoice", invoiceId],
    enabled: Boolean(invoiceId),
    queryFn: async () => {
      const { data } = await api.get<InvoiceDetailResponse>(`/api/v1/cliente/invoices/${invoiceId}`);
      return data;
    },
  });
}
