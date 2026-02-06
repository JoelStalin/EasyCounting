import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export interface PlatformUserItem {
  id: number;
  email: string;
  role: string;
  scope: "PLATFORM";
}

export function usePlatformUsers() {
  return useQuery({
    queryKey: ["admin", "platform-users"],
    queryFn: async () => {
      const { data } = await api.get<PlatformUserItem[]>("/api/v1/admin/users");
      return data;
    },
  });
}
