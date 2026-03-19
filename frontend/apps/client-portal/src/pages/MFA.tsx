import { FormEvent, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { api } from "../api/client";
import { useAuth } from "../auth/use-auth";
import type { AuthSession } from "../store/auth-store";

interface LocationState {
  challengeId?: string;
  returnTo?: string;
}

export function MFAPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setSession } = useAuth();
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const challengeId = (location.state as LocationState | undefined)?.challengeId;
  const returnTo = (location.state as LocationState | undefined)?.returnTo;

  useEffect(() => {
    if (!challengeId) {
      navigate("/login", { replace: true });
    }
  }, [challengeId, navigate]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<AuthSession & { permissions: string[] }>("/auth/mfa/verify", {
        challenge_id: challengeId,
        code,
      });
      setSession({
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        user: data.user,
        permissions: data.permissions,
      });
      if (data.user.onboardingStatus && data.user.onboardingStatus !== "completed") {
        navigate("/onboarding", { replace: true });
        return;
      }
      navigate(returnTo ?? "/dashboard", { replace: true });
    } catch {
      setError("Codigo invalido o expirado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-2 text-center">
          <CardTitle>Verificacion MFA</CardTitle>
          <p className="text-sm text-slate-300">Confirma tu identidad para emitir e-CF y RFCE.</p>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="mfa-code">Codigo</Label>
                <Input
                  id="mfa-code"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  className="text-center text-lg tracking-[0.35em]"
                  value={code}
                  onChange={(event) => setCode(event.target.value)}
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
