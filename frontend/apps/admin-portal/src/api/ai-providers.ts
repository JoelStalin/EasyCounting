import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export type AIProviderType = "openai" | "gemini" | "openai_compatible";

export interface AIProvider {
  id: number;
  displayName: string;
  providerType: AIProviderType;
  enabled: boolean;
  isDefault: boolean;
  baseUrl: string | null;
  model: string;
  apiKeyConfigured: boolean;
  apiKeyMasked: string | null;
  organizationId: string | null;
  projectId: string | null;
  apiVersion: string | null;
  systemPrompt: string | null;
  extraHeaders: Record<string, string>;
  timeoutSeconds: number;
  maxCompletionTokens: number;
  createdAt: string;
  updatedAt: string;
}

export interface AIProviderPayload {
  displayName: string;
  providerType: AIProviderType;
  enabled: boolean;
  isDefault: boolean;
  baseUrl?: string | null;
  model: string;
  apiKey?: string;
  clearApiKey?: boolean;
  organizationId?: string | null;
  projectId?: string | null;
  apiVersion?: string | null;
  systemPrompt?: string | null;
  extraHeaders?: Record<string, string> | null;
  timeoutSeconds: number;
  maxCompletionTokens: number;
}

export function useAIProviders() {
  return useQuery({
    queryKey: ["admin", "ai-providers"],
    queryFn: async () => {
      const { data } = await api.get<AIProvider[]>("/api/v1/admin/ai-providers");
      return data;
    },
  });
}

export function useCreateAIProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: AIProviderPayload) => {
      const { data } = await api.post<AIProvider>("/api/v1/admin/ai-providers", payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
    },
  });
}

export function useUpdateAIProvider(providerId: number | null) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: AIProviderPayload) => {
      const { data } = await api.put<AIProvider>(`/api/v1/admin/ai-providers/${providerId}`, payload);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
    },
  });
}

export function useDeleteAIProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (providerId: number) => {
      await api.delete(`/api/v1/admin/ai-providers/${providerId}`);
      return providerId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "ai-providers"] });
    },
  });
}
