import { useQuery } from "@tanstack/react-query";
import { api } from "./client";
import { useMutation, useQueryClient } from "@tanstack/react-query";

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
  ri_pdf_path?: string | null;
  receptor_nombre?: string | null;
  codigo_seguridad: string | null;
  contabilizado: boolean;
  accounted_at: string | null;
  asiento_referencia: string | null;
}

export interface InvoiceLinePayload {
  descripcion: string;
  cantidad: number;
  precioUnitario: number;
  unidadMedida?: string | null;
  itbisRate?: number | null;
  discountAmount?: number;
}

export interface InvoiceEmitPayload {
  encf?: string | null;
  tipoEcf: string;
  rncReceptor?: string | null;
  receptorNombre?: string | null;
  receptorEmail?: string | null;
  total: number;
  fechaEmision?: string | null;
  lineItems: InvoiceLinePayload[];
  xmlSignedBase64?: string | null;
}

export interface InvoiceEmitResponse {
  invoiceId: number;
  tenantId: number;
  encf: string;
  estadoDgii: string;
  trackId: string;
  total: number;
  message: string;
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

export function useEmitInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: InvoiceEmitPayload) => {
      const { data } = await api.post<InvoiceEmitResponse>("/api/v1/cliente/invoices/emit", payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "invoices"] });
    },
  });
}

export function useSendInvoiceEmail() {
  return useMutation({
    mutationFn: async (payload: { invoiceId: number; recipient: string }) => {
      const { data } = await api.post<{ status: string; message: string }>(
        `/api/v1/cliente/invoices/${payload.invoiceId}/send-email`,
        { recipient: payload.recipient },
      );
      return data;
    },
  });
}
