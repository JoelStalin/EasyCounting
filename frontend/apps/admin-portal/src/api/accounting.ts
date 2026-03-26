import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export interface TenantSettings {
  moneda: string;
  cuenta_ingresos: string | null;
  cuenta_itbis: string | null;
  cuenta_retenciones: string | null;
  dias_credito: number;
  correo_facturacion: string | null;
  telefono_contacto: string | null;
  notas: string | null;
  rounding_policy: string;
  odoo_sync_enabled: boolean;
  odoo_api_url: string | null;
  odoo_database: string | null;
  odoo_company_id: number | null;
  odoo_sales_journal_id: number | null;
  odoo_purchase_journal_id: number | null;
  odoo_fiscal_position_id: number | null;
  odoo_payment_term_id: number | null;
  odoo_currency_id: number | null;
  odoo_customer_document_type_id: number | null;
  odoo_vendor_document_type_id: number | null;
  odoo_credit_note_document_type_id: number | null;
  odoo_debit_note_document_type_id: number | null;
  odoo_sales_tax_id: number | null;
  odoo_purchase_tax_id: number | null;
  odoo_zero_tax_id: number | null;
  odoo_partner_vat_prefix: string | null;
  odoo_journal_code_hint: string | null;
  odoo_api_key_ref: string | null;
  updated_at: string;
}

export interface TenantSettingsUpdate {
  moneda: string;
  cuenta_ingresos: string | null;
  cuenta_itbis: string | null;
  cuenta_retenciones: string | null;
  dias_credito: number;
  correo_facturacion: string | null;
  telefono_contacto: string | null;
  notas: string | null;
  rounding_policy: string;
  odoo_sync_enabled: boolean;
  odoo_api_url: string | null;
  odoo_database: string | null;
  odoo_company_id: number | null;
  odoo_sales_journal_id: number | null;
  odoo_purchase_journal_id: number | null;
  odoo_fiscal_position_id: number | null;
  odoo_payment_term_id: number | null;
  odoo_currency_id: number | null;
  odoo_customer_document_type_id: number | null;
  odoo_vendor_document_type_id: number | null;
  odoo_credit_note_document_type_id: number | null;
  odoo_debit_note_document_type_id: number | null;
  odoo_sales_tax_id: number | null;
  odoo_purchase_tax_id: number | null;
  odoo_zero_tax_id: number | null;
  odoo_partner_vat_prefix: string | null;
  odoo_journal_code_hint: string | null;
  odoo_api_key_ref: string | null;
}

export interface LedgerTotals {
  total_emitidos: number;
  total_aceptados: number;
  total_rechazados: number;
  total_monto: string;
}

export interface LedgerStatusBreakdown {
  contabilizados: number;
  pendientes: number;
}

export interface LedgerMonthlyStat {
  periodo: string;
  cantidad: number;
  monto: string;
}

export interface AccountingSummary {
  totales: LedgerTotals;
  contabilidad: LedgerStatusBreakdown;
  series: LedgerMonthlyStat[];
}

export interface LedgerEntryItem {
  id: number;
  invoiceId?: number | null;
  invoice_id?: number | null;
  encf: string | null;
  referencia: string;
  cuenta: string;
  descripcion: string | null;
  debit: string;
  credit: string;
  fecha: string;
}

export interface LedgerPaginatedResponse {
  items: LedgerEntryItem[];
  total: number;
  page: number;
  size: number;
}

export interface LedgerEntryCreatePayload {
  invoice_id: number | null;
  referencia: string;
  cuenta: string;
  descripcion: string | null;
  debit: string;
  credit: string;
  fecha: string;
}

export function useTenantSettings(tenantId?: string) {
  return useQuery({
    queryKey: ["admin", "tenant-settings", tenantId],
    enabled: Boolean(tenantId),
    queryFn: async () => {
      const { data } = await api.get<TenantSettings>(`/api/v1/admin/tenants/${tenantId}/settings`);
      return data;
    },
  });
}

export function useUpdateTenantSettings(tenantId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantSettingsUpdate) => {
      const { data } = await api.put<TenantSettings>(`/api/v1/admin/tenants/${tenantId}/settings`, payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "tenant-settings", tenantId] });
    },
  });
}

export function useAccountingSummary(tenantId?: string) {
  return useQuery({
    queryKey: ["admin", "accounting-summary", tenantId],
    enabled: Boolean(tenantId),
    queryFn: async () => {
      const { data } = await api.get<AccountingSummary>(`/api/v1/admin/tenants/${tenantId}/accounting/summary`);
      return data;
    },
  });
}

export function useLedgerEntries(tenantId?: string, page = 1, size = 20) {
  return useQuery({
    queryKey: ["admin", "ledger-entries", tenantId, page, size],
    enabled: Boolean(tenantId),
    queryFn: async () => {
      const { data } = await api.get<LedgerPaginatedResponse>(`/api/v1/admin/tenants/${tenantId}/accounting/ledger`, {
        params: { page, size },
      });
      return data;
    },
  });
}

export function useCreateLedgerEntry(tenantId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LedgerEntryCreatePayload) => {
      const { data } = await api.post<LedgerEntryItem>(`/api/v1/admin/tenants/${tenantId}/accounting/ledger`, payload);
      return data;
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin", "ledger-entries", tenantId] }),
        queryClient.invalidateQueries({ queryKey: ["admin", "accounting-summary", tenantId] }),
      ]);
    },
  });
}
