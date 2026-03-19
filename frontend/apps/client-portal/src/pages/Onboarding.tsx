import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { useCompleteOnboardingMutation, useOnboardingQuery } from "../api/onboarding";
import { useAuth } from "../auth/use-auth";

export function OnboardingPage() {
  const navigate = useNavigate();
  const { accessToken, refreshToken, permissions, setSession, user } = useAuth();
  const onboardingQuery = useOnboardingQuery(Boolean(user));
  const completeMutation = useCompleteOnboardingMutation();
  const [companyName, setCompanyName] = useState("");
  const [rnc, setRnc] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (!onboardingQuery.data) {
      return;
    }
    setCompanyName(onboardingQuery.data.companyName);
    setRnc(onboardingQuery.data.rnc);
    setContactEmail(onboardingQuery.data.contactEmail ?? "");
    setContactPhone(onboardingQuery.data.contactPhone ?? "");
    setNotes(onboardingQuery.data.notes ?? "");
  }, [onboardingQuery.data]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const updated = await completeMutation.mutateAsync({
      companyName,
      rnc,
      contactEmail,
      contactPhone,
      notes,
    });
    if (accessToken && refreshToken && user) {
      setSession({
        accessToken,
        refreshToken,
        permissions,
        user: {
          ...user,
          onboardingStatus: updated.onboardingStatus,
        },
      });
    }
    navigate("/dashboard", { replace: true });
  };

  return (
    <div className="space-y-6" data-tour="client-onboarding">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Configura tu emisor</h1>
        <p className="text-sm text-slate-300">
          Completa estos datos antes de habilitar operaciones fiscales reales y certificados.
        </p>
      </header>
      <Card>
        <CardHeader>
          <CardTitle>Onboarding fiscal</CardTitle>
        </CardHeader>
        <CardContent>
          {onboardingQuery.isLoading ? (
            <Spinner label="Cargando onboarding" />
          ) : (
            <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="company-name">Nombre comercial</Label>
                <Input id="company-name" value={companyName} onChange={(event: ChangeEvent<HTMLInputElement>) => setCompanyName(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="company-rnc">RNC</Label>
                <Input id="company-rnc" value={rnc} onChange={(event: ChangeEvent<HTMLInputElement>) => setRnc(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact-email">Correo fiscal</Label>
                <Input id="contact-email" value={contactEmail} onChange={(event: ChangeEvent<HTMLInputElement>) => setContactEmail(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="contact-phone">Telefono</Label>
                <Input id="contact-phone" value={contactPhone} onChange={(event: ChangeEvent<HTMLInputElement>) => setContactPhone(event.target.value)} />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="notes">Notas</Label>
                <textarea
                  id="notes"
                  className="min-h-28 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                  value={notes}
                  onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setNotes(event.target.value)}
                />
              </div>
              <div className="md:col-span-2 flex justify-end">
                <Button type="submit" disabled={completeMutation.isPending}>
                  {completeMutation.isPending ? <Spinner label="Guardando" /> : "Completar onboarding"}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
