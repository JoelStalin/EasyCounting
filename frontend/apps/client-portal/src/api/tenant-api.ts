import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export type TenantApiAccessMode = "read" | "read_write";

export interface TenantApiTokenItem {
  id: number;
  name: string;
  tokenPrefix: string;
  scopes: string[];
  lastUsedAt: string | null;
  expiresAt: string | null;
  revokedAt: string | null;
  createdAt: string;
  createdByEmail: string | null;
}

export interface TenantApiTokenCreatePayload {
  name: string;
  accessMode: TenantApiAccessMode;
  expiresInDays?: number | null;
}

export interface TenantApiTokenCreateResponse extends TenantApiTokenItem {
  token: string;
}

export function useTenantApiTokens() {
  return useQuery({
    queryKey: ["tenant", "api-tokens"],
    queryFn: async () => {
      const { data } = await api.get<TenantApiTokenItem[]>("/api/v1/cliente/api-tokens");
      return data;
    },
  });
}

export function useCreateTenantApiToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantApiTokenCreatePayload) => {
      const { data } = await api.post<TenantApiTokenCreateResponse>("/api/v1/cliente/api-tokens", payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "api-tokens"] });
    },
  });
}

export function useRevokeTenantApiToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tokenId: number) => {
      const { data } = await api.delete<TenantApiTokenItem>(`/api/v1/cliente/api-tokens/${tokenId}`);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "api-tokens"] });
    },
  });
}
