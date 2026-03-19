import { FormEvent, useMemo, useState } from "react";
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label, Spinner } from "@getupsoft/ui";
import { useEmitPartnerInvoice, usePartnerTenants, type PartnerTenantItem } from "../api/partner";

function buildDemoEncf() {
  return `E31${Date.now().toString().slice(-9)}`;
}

export function EmitECFPage() {
  const tenantsQuery = usePartnerTenants();
  const emitMutation = useEmitPartnerInvoice();
  const availableTenants = useMemo(
    () => (tenantsQuery.data ?? []).filter((tenant: PartnerTenantItem) => tenant.canEmit),
    [tenantsQuery.data],
  );
  const [tenantId, setTenantId] = useState("");
  const [encf, setEncf] = useState(buildDemoEncf());
  const [tipoEcf, setTipoEcf] = useState("31");
  const [rncReceptor, setRncReceptor] = useState("101010101");
  const [total, setTotal] = useState("1250.00");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await emitMutation.mutateAsync({
      tenantId: Number(tenantId),
      encf,
      tipoEcf,
      rncReceptor,
      total,
    });
    setEncf(buildDemoEncf());
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
      <Card>
        <CardHeader className="space-y-2">
          <CardTitle>EmisiÃ³n demo controlada</CardTitle>
          <p className="text-sm text-slate-300">
            El seller solo puede generar documentos demo para tenants que tenga asignados con permiso de emisiÃ³n.
          </p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="tenantId">Cliente</Label>
              <select
                id="tenantId"
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                value={tenantId}
                onChange={(event) => setTenantId(event.target.value)}
                required
              >
                <option value="">Selecciona un cliente</option>
                {availableTenants.map((tenant: PartnerTenantItem) => (
                  <option key={tenant.id} value={tenant.id}>
                    {tenant.name} · {tenant.rnc}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="encf">ENCF</Label>
                <Input id="encf" value={encf} onChange={(event) => setEncf(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="tipoEcf">Tipo e-CF</Label>
                <Input id="tipoEcf" value={tipoEcf} onChange={(event) => setTipoEcf(event.target.value)} required />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="rncReceptor">RNC receptor</Label>
                <Input
                  id="rncReceptor"
                  value={rncReceptor}
                  onChange={(event) => setRncReceptor(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="total">Monto total</Label>
                <Input id="total" value={total} onChange={(event) => setTotal(event.target.value)} required />
              </div>
            </div>
            <Button className="w-full" type="submit" disabled={emitMutation.isPending || availableTenants.length === 0}>
              {emitMutation.isPending ? <Spinner label="Generando" /> : "Generar comprobante demo"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="space-y-2">
          <CardTitle>Resultado y reglas</CardTitle>
          <p className="text-sm text-slate-300">Esta superficie estÃ¡ limitada por rol y por asignaciÃ³n de tenants.</p>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-slate-300">
          <ul className="space-y-2">
            <li>• `partner_reseller` y `partner_operator` pueden emitir solo si la asignaciÃ³n habilita `canEmit`.</li>
            <li>• `partner_auditor` conserva acceso de lectura, sin emisiÃ³n.</li>
            <li>• Los documentos se crean en estado `SIMULADO` dentro del backend demo.</li>
          </ul>
          {emitMutation.isSuccess ? (
            <div className="rounded-xl border border-emerald-900/60 bg-emerald-950/30 p-4 text-emerald-200">
              <p className="font-medium">{emitMutation.data.message}</p>
              <p className="mt-2 font-mono text-xs">Track: {emitMutation.data.trackId}</p>
              <p className="font-mono text-xs">ENCF: {emitMutation.data.encf}</p>
            </div>
          ) : null}
          {emitMutation.isError ? (
            <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-rose-200">
              No se pudo generar el comprobante demo. Verifica el cliente seleccionado y tus permisos.
            </div>
          ) : null}
          {tenantsQuery.isLoading ? <p>Cargando clientes habilitados…</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
