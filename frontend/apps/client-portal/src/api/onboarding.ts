import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface TenantOnboardingStatus {
  tenantId: number;
  onboardingStatus: string;
  companyName: string;
  rnc: string;
  contactEmail: string | null;
  contactPhone: string | null;
  notes: string | null;
  canEmitReal: boolean;
}

export interface CompleteOnboardingPayload {
  companyName: string;
  rnc: string;
  contactEmail?: string | null;
  contactPhone?: string | null;
  notes?: string | null;
}

export function useOnboardingQuery(enabled: boolean) {
  return useQuery({
    queryKey: ["tenant-onboarding"],
    enabled,
    queryFn: async () => {
      const { data } = await api.get<TenantOnboardingStatus>("/api/v1/cliente/onboarding");
      return data;
    },
  });
}

export function useCompleteOnboardingMutation() {
  return useMutation({
    mutationFn: async (payload: CompleteOnboardingPayload) => {
      const { data } = await api.put<TenantOnboardingStatus>("/api/v1/cliente/onboarding", payload);
      return data;
    },
  });
}
