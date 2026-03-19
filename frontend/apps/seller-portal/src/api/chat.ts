import { useMutation } from "@tanstack/react-query";
import { api } from "./client";

export interface ChatSource {
  invoice_id: number;
  encf: string;
  track_id: string | null;
  estado_dgii: string;
  total: string;
  fecha_emision: string;
  snippet: string;
}

export interface ChatAnswerResponse {
  answer: string;
  engine: string;
  tenant_id: number;
  sources: ChatSource[];
  warnings: string[];
}

export interface ChatQuestionRequest {
  question: string;
  max_sources?: number;
}

export function useTenantChat() {
  return useMutation({
    mutationFn: async (payload: ChatQuestionRequest) => {
      const { data } = await api.post<ChatAnswerResponse>("/api/v1/cliente/chat/ask", payload);
      return data;
    },
  });
}
