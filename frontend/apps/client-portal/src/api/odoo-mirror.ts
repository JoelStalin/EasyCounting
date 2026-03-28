import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface OdooSyncPayload {
  includeCustomers: boolean;
  includeVendors: boolean;
  includeProducts: boolean;
  includeInvoices: boolean;
  limit: number;
}

export interface OdooSyncResponse {
  status: string;
  customers: number;
  vendors: number;
  products: number;
  invoices: number;
  message: string;
}

export interface OdooPartnerItem {
  id: number;
  odooId: number;
  partnerKind: string;
  name: string;
  vat?: string | null;
  email?: string | null;
  phone?: string | null;
  companyType?: string | null;
  syncedAt: string;
}

export interface OdooProductItem {
  id: number;
  odooId: number;
  name: string;
  defaultCode?: string | null;
  listPrice: string;
  standardPrice: string;
  active: boolean;
  syncedAt: string;
}

export interface OdooInvoiceItem {
  id: number;
  odooId: number;
  moveName?: string | null;
  moveType?: string | null;
  state?: string | null;
  paymentState?: string | null;
  invoiceDate?: string | null;
  partnerName?: string | null;
  partnerVat?: string | null;
  amountTotal: string;
  amountTax: string;
  amountUntaxed: string;
  encf?: string | null;
  syncedAt: string;
}

export function useSyncOdoo() {
  return useMutation({
    mutationFn: async (payload: Partial<OdooSyncPayload> = {}) => {
      const body: OdooSyncPayload = {
        includeCustomers: payload.includeCustomers ?? true,
        includeVendors: payload.includeVendors ?? true,
        includeProducts: payload.includeProducts ?? true,
        includeInvoices: payload.includeInvoices ?? true,
        limit: payload.limit ?? 100,
      };
      const { data } = await api.post<OdooSyncResponse>("/api/v1/cliente/integrations/odoo/sync", body);
      return data;
    },
  });
}

export function useOdooCustomers(limit = 20) {
  return useQuery({
    queryKey: ["odoo-customers", limit],
    queryFn: async () => {
      const { data } = await api.get<OdooPartnerItem[]>("/api/v1/cliente/integrations/odoo/customers", { params: { limit } });
      return data;
    },
  });
}

export function useOdooVendors(limit = 20) {
  return useQuery({
    queryKey: ["odoo-vendors", limit],
    queryFn: async () => {
      const { data } = await api.get<OdooPartnerItem[]>("/api/v1/cliente/integrations/odoo/vendors", { params: { limit } });
      return data;
    },
  });
}

export function useOdooProducts(limit = 20) {
  return useQuery({
    queryKey: ["odoo-products", limit],
    queryFn: async () => {
      const { data } = await api.get<OdooProductItem[]>("/api/v1/cliente/integrations/odoo/products", { params: { limit } });
      return data;
    },
  });
}

export function useOdooInvoices(limit = 20) {
  return useQuery({
    queryKey: ["odoo-invoices", limit],
    queryFn: async () => {
      const { data } = await api.get<OdooInvoiceItem[]>("/api/v1/cliente/integrations/odoo/invoices", { params: { limit } });
      return data;
    },
  });
}
