import { FormEvent, useMemo, useState } from "react";
import { useAuth } from "../auth/use-auth";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";
import { useEmitInvoice } from "../api/invoices";
import { useFormTutor } from "../tutorial/hooks/useFormTutor";
import { TutorContextualIcon } from "../tutorial/components/TutorContextualIcon";
import { EmitEcfTutorConfig } from "../tutorial/config/emitEcfTutor";

export function EmitECFPage() {
  const { hasPermission } = useAuth();
  const emitMutation = useEmitInvoice();

  const [encf, setEncf] = useState("");
  const [tipoEcf, setTipoEcf] = useState("31");
  const [rncReceptor, setRncReceptor] = useState("");
  const [receptorNombre, setReceptorNombre] = useState("");
  const [receptorEmail, setReceptorEmail] = useState("");
  const [xmlSignedBase64, setXmlSignedBase64] = useState("");
  const [lineItems, setLineItems] = useState([
    { descripcion: "Servicio profesional", cantidad: "1", precioUnitario: "1500.00", itbisRate: "0.18" },
  ]);
  const [message, setMessage] = useState<string | null>(null);

  const tutor = useFormTutor(EmitEcfTutorConfig);

  const total = useMemo(() => {
    return lineItems.reduce((acc, item) => {
      const qty = Number(item.cantidad || "0");
      const unit = Number(item.precioUnitario || "0");
      const rate = Number(item.itbisRate || "0");
      const subtotal = qty * unit;
      return acc + subtotal + subtotal * rate;
    }, 0);
  }, [lineItems]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!hasPermission("TENANT_INVOICE_EMIT")) {
      setMessage("No tienes permisos para emitir e-CF.");
      return;
    }
    try {
      const result = await emitMutation.mutateAsync({
        encf: encf.trim() || null,
        tipoEcf,
        rncReceptor: rncReceptor.trim() || null,
        receptorNombre: receptorNombre.trim() || null,
        receptorEmail: receptorEmail.trim() || null,
        total,
        lineItems: lineItems.map((item) => ({
          descripcion: item.descripcion,
          cantidad: Number(item.cantidad || "0"),
          precioUnitario: Number(item.precioUnitario || "0"),
          itbisRate: Number(item.itbisRate || "0"),
        })),
        xmlSignedBase64: xmlSignedBase64.trim() || null,
      });
      setMessage(`e-CF enviado a DGII. ENCF: ${result.encf} (TrackId: ${result.trackId})`);
      setEncf("");
      setXmlSignedBase64("");
    } catch {
      setMessage("No se pudo emitir el e-CF. Revisa datos de factura y configuracion fiscal.");
    }
  };

  return (
    <RequirePermission anyOf={["TENANT_INVOICE_EMIT"]}>
      <div className="space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold text-white flex items-center gap-3">
            Emitir e-CF
            {!tutor.isActive && (
              <button
                onClick={tutor.restartTutor}
                className="text-xs bg-slate-800 text-primary px-3 py-1 rounded-full border border-slate-700 hover:bg-slate-700 transition"
              >
                Iniciar Tutorial
              </button>
            )}
          </h1>
          <p className="text-sm text-slate-300">Genera facturas con productos/servicios y secuencia DGII controlada.</p>

          {tutor.isActive && (
            <div className="bg-primary/10 border border-primary/30 p-4 rounded-xl mb-4 relative overflow-hidden">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-sm font-bold text-primary mb-1">{tutor.config.title}</h3>
                  <p className="text-xs text-slate-300 mb-3">{tutor.config.description}</p>
                </div>
                <button onClick={() => tutor.dismissTutor(true)} className="text-xs text-slate-400 hover:text-white underline">
                  Omitir y no volver a mostrar
                </button>
              </div>
              <p className="text-xs text-primary font-semibold">Pasa el raton sobre los botones (?) para ayuda contextual.</p>
            </div>
          )}
        </header>

        <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-border bg-slate-900/40 p-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <label className="block space-y-2 text-sm text-foreground" id="tour-step-tipo-ecf">
              <span className="font-semibold text-slate-200 flex items-center">
                Tipo de e-CF <span className="text-red-400 ml-1">*</span>
                {tutor.isActive && tutor.getFieldHelper("tipo-ecf") && <TutorContextualIcon info={tutor.getFieldHelper("tipo-ecf")!} />}
              </span>
              <select
                value={tipoEcf}
                onChange={(event) => setTipoEcf(event.target.value)}
                className="w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                required
              >
                <option value="31">31 - e-CF Factura de Credito Fiscal</option>
                <option value="32">32 - e-CF Factura de Consumo</option>
                <option value="33">33 - e-CF Nota de Debito</option>
                <option value="34">34 - e-CF Nota de Credito</option>
              </select>
            </label>

            <label className="block space-y-2 text-sm text-foreground" id="tour-step-rnc">
              <span className="font-semibold text-slate-200 flex items-center">
                RNC o Cedula del Comprador <span className="text-red-400 ml-1">*</span>
                {tutor.isActive && tutor.getFieldHelper("comprador-rnc") && <TutorContextualIcon info={tutor.getFieldHelper("comprador-rnc")!} />}
              </span>
              <input
                type="text"
                maxLength={11}
                value={rncReceptor}
                onChange={(event) => setRncReceptor(event.target.value)}
                className="w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                placeholder="Ej: 101000000"
                required
              />
            </label>

            <label className="block space-y-2 text-sm text-foreground" id="tour-step-monto">
              <span className="font-semibold text-slate-200 flex items-center">
                Cobro Total (RD$) <span className="text-red-400 ml-1">*</span>
                {tutor.isActive && tutor.getFieldHelper("total-monto") && <TutorContextualIcon info={tutor.getFieldHelper("total-monto")!} />}
              </span>
              <input
                type="number"
                step="0.01"
                value={total.toFixed(2)}
                readOnly
                className="w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none"
              />
            </label>

            <label className="block space-y-2 text-sm text-foreground" id="tour-step-itbis">
              <span className="font-semibold text-slate-200">ITBIS Facturado (RD$)</span>
              <input
                type="number"
                step="0.01"
                value={(total * 0.18).toFixed(2)}
                readOnly
                className="w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none"
              />
            </label>
          </div>

          <div className="space-y-3 rounded-md border border-slate-700 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-200">Productos / Servicios</span>
              <button
                type="button"
                className="rounded border border-slate-700 px-2 py-1 text-xs text-slate-200"
                onClick={() =>
                  setLineItems((prev) => [
                    ...prev,
                    { descripcion: "", cantidad: "1", precioUnitario: "0.00", itbisRate: "0.18" },
                  ])
                }
              >
                Agregar linea
              </button>
            </div>
            {lineItems.map((line, idx) => (
              <div key={`line-${idx}`} className="grid grid-cols-1 gap-2 md:grid-cols-4">
                <input
                  value={line.descripcion}
                  onChange={(event) =>
                    setLineItems((prev) => prev.map((row, i) => (i === idx ? { ...row, descripcion: event.target.value } : row)))
                  }
                  className="rounded-md border border-input bg-slate-950 px-3 py-2 text-sm"
                  placeholder="Descripcion"
                />
                <input
                  value={line.cantidad}
                  onChange={(event) =>
                    setLineItems((prev) => prev.map((row, i) => (i === idx ? { ...row, cantidad: event.target.value } : row)))
                  }
                  className="rounded-md border border-input bg-slate-950 px-3 py-2 text-sm"
                  type="number"
                  step="0.01"
                  placeholder="Cantidad"
                />
                <input
                  value={line.precioUnitario}
                  onChange={(event) =>
                    setLineItems((prev) => prev.map((row, i) => (i === idx ? { ...row, precioUnitario: event.target.value } : row)))
                  }
                  className="rounded-md border border-input bg-slate-950 px-3 py-2 text-sm"
                  type="number"
                  step="0.01"
                  placeholder="Precio unitario"
                />
                <input
                  value={line.itbisRate}
                  onChange={(event) =>
                    setLineItems((prev) => prev.map((row, i) => (i === idx ? { ...row, itbisRate: event.target.value } : row)))
                  }
                  className="rounded-md border border-input bg-slate-950 px-3 py-2 text-sm"
                  type="number"
                  step="0.0001"
                  placeholder="ITBIS rate"
                />
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <input
              value={encf}
              onChange={(event) => setEncf(event.target.value)}
              className="rounded-md border border-input bg-slate-950 px-3 py-2 text-sm"
              placeholder="ENCF manual (opcional)"
            />
            <input
              value={receptorNombre}
              onChange={(event) => setReceptorNombre(event.target.value)}
              className="rounded-md border border-input bg-slate-950 px-3 py-2 text-sm"
              placeholder="Nombre receptor"
            />
            <input
              value={receptorEmail}
              onChange={(event) => setReceptorEmail(event.target.value)}
              className="rounded-md border border-input bg-slate-950 px-3 py-2 text-sm"
              placeholder="Correo receptor"
              type="email"
            />
          </div>

          <label className="block space-y-2 text-sm text-foreground" id="tour-step-payload">
            <span className="font-semibold text-slate-200">XML firmado en base64 (opcional)</span>
            <textarea
              value={xmlSignedBase64}
              onChange={(event) => setXmlSignedBase64(event.target.value)}
              className="h-32 w-full rounded-md border border-input bg-slate-950 px-3 py-2 font-mono text-xs focus:border-primary focus:outline-none"
              placeholder="Pega aqui XML firmado si ya lo tienes."
            />
          </label>

          <label className="flex items-center gap-3 text-sm text-foreground" id="tour-step-sync">
            <input type="checkbox" className="h-4 w-4 rounded border-input bg-slate-950 text-primary accent-primary" defaultChecked />
            <span className="font-semibold text-slate-200 flex items-center">
              Transmision agil (directa) a DGII
              {tutor.isActive && tutor.getFieldHelper("transmision-agil") && <TutorContextualIcon info={tutor.getFieldHelper("transmision-agil")!} />}
            </span>
          </label>

          <div className="flex justify-end pt-4 border-t border-border">
            <button
              id="tour-step-submit"
              className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90"
              type="submit"
              disabled={emitMutation.isPending}
            >
              {emitMutation.isPending ? <Spinner label="Procesando Validacion" /> : "Validar y Emitir e-CF"}
            </button>
          </div>
        </form>
        {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      </div>
    </RequirePermission>
  );
}
