import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export type RecurringFrequency = "daily" | "biweekly" | "monthly" | "custom";
export type RecurringStatus = "active" | "paused" | "completed" | "cancelled";

export interface RecurringInvoiceExecution {
  id: number;
  invoiceId: number | null;
  scheduledFor: string;
  executedAt: string;
  status: string;
  errorMessage: string | null;
}

export interface RecurringInvoiceSchedule {
  id: number;
  name: string;
  status: RecurringStatus;
  frequency: RecurringFrequency;
  customIntervalDays: number | null;
  startAt: string;
  endAt: string | null;
  nextRunAt: string | null;
  lastRunAt: string | null;
  tipoEcf: string;
  rncReceptor: string | null;
  total: string;
  notes: string | null;
  lastGeneratedInvoiceId: number | null;
  createdAt: string;
  updatedAt: string;
  executions: RecurringInvoiceExecution[];
}

export interface RecurringInvoicePayload {
  name: string;
  frequency: RecurringFrequency;
  customIntervalDays?: number | null;
  startAt: string;
  endAt?: string | null;
  tipoEcf: string;
  rncReceptor?: string | null;
  total: string;
  notes?: string | null;
}

export interface RecurringInvoiceRunSummary {
  processed: number;
  generated: number;
  failed: number;
  schedules: RecurringInvoiceSchedule[];
}

export function useRecurringInvoices() {
  return useQuery({
    queryKey: ["tenant", "recurring-invoices"],
    queryFn: async () => {
      const { data } = await api.get<RecurringInvoiceSchedule[]>("/api/v1/cliente/recurring-invoices");
      return data;
    },
  });
}

export function useCreateRecurringInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: RecurringInvoicePayload) => {
      const { data } = await api.post<RecurringInvoiceSchedule>("/api/v1/cliente/recurring-invoices", payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "recurring-invoices"] });
      await queryClient.invalidateQueries({ queryKey: ["tenant", "invoices"] });
    },
  });
}

export function usePauseRecurringInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (scheduleId: number) => {
      const { data } = await api.post<RecurringInvoiceSchedule>(`/api/v1/cliente/recurring-invoices/${scheduleId}/pause`);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "recurring-invoices"] });
    },
  });
}

export function useResumeRecurringInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (scheduleId: number) => {
      const { data } = await api.post<RecurringInvoiceSchedule>(`/api/v1/cliente/recurring-invoices/${scheduleId}/resume`);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "recurring-invoices"] });
    },
  });
}

export function useRunDueRecurringInvoices() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<RecurringInvoiceRunSummary>("/api/v1/cliente/recurring-invoices/run-due");
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "recurring-invoices"] });
      await queryClient.invalidateQueries({ queryKey: ["tenant", "invoices"] });
      await queryClient.invalidateQueries({ queryKey: ["tenant", "usage"] });
    },
  });
}
