import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { api } from "../api/client";
import { useAuth } from "../auth/use-auth";
import type { AuthSession } from "../store/auth-store";

interface LocationState {
  email: string;
}

export function MFAPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setSession } = useAuth();
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const email = (location.state as LocationState | undefined)?.email;

  useEffect(() => {
    if (!email) {
      navigate("/login", { replace: true });
    }
  }, [email, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<AuthSession & { permissions: string[] }>("/auth/mfa/verify", {
        email,
        code,
      });
      setSession({
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        user: data.user,
        permissions: data.permissions,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError("Código inválido o expirado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-2 text-center">
          <CardTitle>Verificación MFA</CardTitle>
          <p className="text-sm text-slate-300">Ingresa el código TOTP generado en tu dispositivo seguro.</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="mfa-code">Código</Label>
                <Input
                  id="mfa-code"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  className="text-center text-lg tracking-[0.35em]"
                  value={code}
                  onChange={(event: ChangeEvent<HTMLInputElement>) => setCode(event.target.value)}
                  required
                />
              </div>
            </div>
            <Button className="w-full" type="submit" disabled={loading}>
              {loading ? <Spinner label="Verificando" /> : "Confirmar"}
            </Button>
            {error ? <p className="text-center text-sm text-red-400">{error}</p> : null}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
