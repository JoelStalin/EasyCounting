import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface UserViewTourItem {
  viewKey: string;
  tourVersion: number;
  status: "pending" | "completed" | "dismissed";
  lastStep: number | null;
  completedAt: string | null;
}

export function useMyToursQuery(enabled: boolean) {
  return useQuery({
    queryKey: ["ui-tours", "me", "seller"],
    enabled,
    queryFn: async () => {
      const { data } = await api.get<UserViewTourItem[]>("/api/v1/ui-tours/me");
      return data;
    },
  });
}

export function useUpsertTourMutation() {
  return useMutation({
    mutationFn: async (payload: { viewKey: string; tourVersion: number; status: string; lastStep: number | null }) => {
      const { data } = await api.put<UserViewTourItem>(`/api/v1/ui-tours/${payload.viewKey}`, {
        tourVersion: payload.tourVersion,
        status: payload.status,
        lastStep: payload.lastStep,
      });
      return data;
    },
  });
}
