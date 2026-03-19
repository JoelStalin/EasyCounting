import { ReactNode, useEffect } from "react";
import { useAuthStore } from "../store/auth-store";
import { Spinner } from "../components/Spinner";

interface Props {
  children: ReactNode;
}

export function AuthProvider({ children }: Props) {
  const hydrate = useAuthStore((state) => state.hydrate);
  const hydrated = useAuthStore((state) => state.hydrated);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  if (!hydrated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner label="Preparando sesión" />
      </div>
    );
  }

  return <>{children}</>;
}
