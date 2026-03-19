import { Navigate, useLocation } from "react-router-dom";
import { ReactNode } from "react";
import { useAuth } from "./use-auth";
import { ForbiddenState } from "../components/ForbiddenState";
import { Spinner } from "../components/Spinner";

interface RequireAuthProps {
  children: ReactNode;
}

export function RequireAuth({ children }: RequireAuthProps) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner label="Verificando sesión" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}

interface RequirePermissionProps {
  anyOf: string[];
  children: ReactNode;
}

export function RequirePermission({ anyOf, children }: RequirePermissionProps) {
  const { hasAnyPermission, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner label="Verificando permisos" />
      </div>
    );
  }

  if (!hasAnyPermission(anyOf)) {
    return <ForbiddenState />;
  }

  return <>{children}</>;
}

interface RequireScopeProps {
  scope: "PLATFORM" | "TENANT";
  children: ReactNode;
}

export function RequireScope({ scope, children }: RequireScopeProps) {
  const { scope: currentScope, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner label="Cargando" />
      </div>
    );
  }

  if (currentScope !== scope) {
    return <ForbiddenState description="Esta sección pertenece a otro tipo de cuenta." />;
  }

  return <>{children}</>;
}

interface RequireOnboardingCompleteProps {
  children: ReactNode;
}

export function RequireOnboardingComplete({ children }: RequireOnboardingCompleteProps) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Spinner label="Cargando" />
      </div>
    );
  }

  if (user?.onboardingStatus && user.onboardingStatus !== "completed" && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
}

interface RequireMFAProps {
  children: ReactNode;
  mfaCompleted: boolean;
}

export function RequireMFA({ children, mfaCompleted }: RequireMFAProps) {
  if (!mfaCompleted) {
    return <ForbiddenState description="Completa MFA para emitir comprobantes." />;
  }
  return <>{children}</>;
}
