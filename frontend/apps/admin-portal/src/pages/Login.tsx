import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { startSocialLogin, useLoginMutation, useSocialProvidersQuery } from "../api/auth";
import { useAuth } from "../auth/use-auth";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const { mutateAsync, isPending, isError } = useLoginMutation();
  const { isAuthenticated } = useAuth();
  const providersQuery = useSocialProvidersQuery();

  const from = useMemo(() => {
    const state = location.state as { from?: { pathname?: string } } | undefined;
    return state?.from?.pathname ?? "/dashboard";
  }, [location.state]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [from, isAuthenticated, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const response = await mutateAsync({ email, password });
    if (response.mfa_required) {
      navigate("/mfa", { state: { challengeId: response.challenge_id, returnTo: from } });
      return;
    }
    navigate(from, { replace: true });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-2 text-center">
          <CardTitle>EasyCounting Admin</CardTitle>
          <p className="text-sm text-slate-300">Autenticacion multi-factor con controles RBAC.</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Correo electronico</Label>
                <Input
                  data-tour="login-email"
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event: ChangeEvent<HTMLInputElement>) => setEmail(event.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Contrasena</Label>
                <Input
                  data-tour="login-password"
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event: ChangeEvent<HTMLInputElement>) => setPassword(event.target.value)}
                  required
                />
              </div>
            </div>
            <Button className="w-full" type="submit" disabled={isPending} data-tour="login-submit">
              {isPending ? <Spinner label="Validando" /> : "Ingresar"}
            </Button>
            {providersQuery.data && providersQuery.data.length > 0 ? (
              <div className="space-y-2 border-t border-slate-800 pt-4" data-tour="login-social">
                {providersQuery.data.map((provider) => (
                  <button
                    key={provider.provider}
                    type="button"
                    className="w-full rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:border-primary hover:text-primary"
                    onClick={() => startSocialLogin(provider.provider, from)}
                  >
                    Continuar con {provider.label}
                  </button>
                ))}
              </div>
            ) : null}
            {isError ? <p className="text-center text-sm text-red-400">Credenciales invalidas o MFA requerido.</p> : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
