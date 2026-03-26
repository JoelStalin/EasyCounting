import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export interface TenantCertificateItem {
  id: number;
  alias: string;
  subject: string;
  issuer: string;
  notBefore: string;
  notAfter: string;
  isActive: boolean;
}

export interface TenantCertificateListResponse {
  items: TenantCertificateItem[];
  activeCertificateId: number | null;
  activeSource: string | null;
}

export interface TenantCertificateUploadPayload {
  alias: string;
  password: string;
  activate?: boolean;
  certificate: File;
}

export interface TenantCertificateUploadResponse extends TenantCertificateItem {
  message: string;
}

export function useTenantCertificates() {
  return useQuery({
    queryKey: ["tenant", "certificates"],
    queryFn: async () => {
      const { data } = await api.get<TenantCertificateListResponse>("/api/v1/cliente/certificates");
      return data;
    },
  });
}

export function useUploadTenantCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantCertificateUploadPayload) => {
      const formData = new FormData();
      formData.append("alias", payload.alias);
      formData.append("password", payload.password);
      formData.append("activate", payload.activate === false ? "false" : "true");
      formData.append("certificate", payload.certificate);
      const { data } = await api.post<TenantCertificateUploadResponse>("/api/v1/cliente/certificates", formData);
      return data;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["tenant", "certificates"] });
    },
  });
}
