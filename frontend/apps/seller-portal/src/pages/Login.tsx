import { FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { startSocialLogin, useLoginMutation, useSocialProvidersQuery } from "../api/auth";
import { useAuth } from "../auth/use-auth";

const DEMO_ACCOUNTS = [
  {
    title: "Revendedor demo",
    email: "seller@getupsoft.com.do",
    password: "Seller123!",
    note: "Puede ver clientes asignados y emitir demo solo en su cartera.",
  },
  {
    title: "Auditor demo",
    email: "seller.auditor@getupsoft.com.do",
    password: "SellerAudit123!",
    note: "Mismo alcance de cartera, pero sin permiso de emision.",
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
    <div className="grid min-h-screen gap-6 bg-slate-950 px-4 py-10 xl:grid-cols-[1.1fr,0.9fr]">
      <div className="flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-2 text-center">
            <CardTitle>EasyCounting Socios</CardTitle>
            <p className="text-sm text-slate-300">
              Portal para revendedores y operadores con acceso restringido a sus clientes.
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
                      Continuar con {provider.label}
                    </button>
                  ))}
                </div>
              ) : null}
              {isError ? (
                <p className="text-center text-sm text-red-400">Credenciales invalidas o cuenta sin perfil seller.</p>
              ) : null}
            </form>
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-center">
        <Card className="w-full max-w-xl">
          <CardHeader className="space-y-2">
            <CardTitle>Modo demo para partners</CardTitle>
            <p className="text-sm text-slate-300">
              Estas credenciales dummy sirven para prospectos y validaciones no fiscales.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
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
              El acceso demo esta aislado del entorno principal y opera con datos ficticios de clientes y comprobantes.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
