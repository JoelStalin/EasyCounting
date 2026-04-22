import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { startSocialLogin, useLoginMutation, useSocialProvidersQuery } from "../api/auth";
import { useAuth } from "../auth/use-auth";
import { DemoStoreNav } from "../components/DemoStoreNav";

const DEMO_ACCOUNTS = [
  {
    title: "Cliente demo",
    email: "cliente@getupsoft.com.do",
    password: "Tenant123!",
    note: "Acceso de prospecto para revisar dashboard, emision simulada y perfil.",
  },
  {
    title: "Operador demo",
    email: "cliente.operador@getupsoft.com.do",
    password: "TenantOps123!",
    note: "Cuenta adicional para validaciones internas y pruebas funcionales.",
  },
];

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const { mutateAsync, isPending, isError } = useLoginMutation();
  const { isAuthenticated } = useAuth();
  const providersQuery = useSocialProvidersQuery();
  const googleProvider = providersQuery.data?.find((provider) => provider.provider === "google") ?? null;

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
    if (response.user.onboarding_status && response.user.onboarding_status !== "completed") {
      navigate("/onboarding", { replace: true });
      return;
    }
    navigate(from, { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <DemoStoreNav
        googleEnabled={Boolean(googleProvider)}
        onGoogleClick={googleProvider ? () => startSocialLogin(googleProvider.provider, "/dashboard") : undefined}
      />
      <div className="grid min-h-screen gap-6 px-4 pb-10 pt-28 xl:grid-cols-[1.05fr,0.95fr]">
        <div className="flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-2 text-center">
            <CardTitle>Galante's Jewelry / Acceso clientes</CardTitle>
            <p className="text-sm text-slate-300">
              Portal de acceso para seguimiento comercial, onboarding y operaciones del cliente.
            </p>
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
                    onChange={(event) => setEmail(event.target.value)}
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
                    onChange={(event) => setPassword(event.target.value)}
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
                      {provider.provider === "google" ? "Crear cuenta o entrar con Google" : `Continuar con ${provider.label}`}
                    </button>
                  ))}
                </div>
              ) : null}
              {providersQuery.isSuccess && providersQuery.data?.length === 0 ? (
                <div className="rounded-xl border border-amber-900/60 bg-amber-950/30 p-4 text-xs text-amber-100">
                  El acceso con Google queda disponible al activar SOCIAL_AUTH_ENABLED, SOCIAL_GOOGLE_ENABLED,
                  SOCIAL_GOOGLE_CLIENT_ID y SOCIAL_GOOGLE_CLIENT_SECRET en el backend.
                </div>
              ) : null}
              {isError ? <p className="text-center text-sm text-red-400">Credenciales invalidas o MFA requerido.</p> : null}
            </form>
          </CardContent>
        </Card>
        </div>

        <div className="flex items-center justify-center">
        <Card className="w-full max-w-xl">
          <CardHeader className="space-y-2">
            <CardTitle>Demo comercial activa</CardTitle>
            <p className="text-sm text-slate-300">
              Usa el catalogo demo y las cuentas de muestra para enseñar onboarding, cotizacion y acceso del cliente.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <Link className="rounded-xl border border-slate-700 px-4 py-3 text-sm font-semibold text-white hover:border-primary hover:text-primary" to="/catalog">
                Ver catalogo demo
              </Link>
              <Link className="rounded-xl border border-slate-700 px-4 py-3 text-sm font-semibold text-white hover:border-primary hover:text-primary" to="/checkout">
                Ver cotizacion demo
              </Link>
            </div>
            {DEMO_ACCOUNTS.map((account) => (
              <div key={account.email} className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                <p className="font-medium text-slate-100">{account.title}</p>
                <p className="mt-1 text-xs text-slate-400">{account.note}</p>
                <button
                  type="button"
                  className="mt-3 w-full rounded-md border border-slate-700 px-3 py-2 text-left text-sm text-slate-200 hover:border-primary hover:text-primary"
                  onClick={() => {
                    setEmail(account.email);
                    setPassword(account.password);
                  }}
                >
                  {account.email}
                  <span className="block font-mono text-xs text-slate-400">{account.password}</span>
                </button>
              </div>
            ))}
            <div className="rounded-xl border border-amber-900/60 bg-amber-950/30 p-4 text-sm text-amber-100">
              Este entorno demo usa datos ficticios y no emite comprobantes fiscales reales.
            </div>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}
