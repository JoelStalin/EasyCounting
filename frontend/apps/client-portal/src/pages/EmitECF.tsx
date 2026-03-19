import { FormEvent, useState } from "react";
import { useAuth } from "../auth/use-auth";
import { RequirePermission } from "../auth/guards";
import { Spinner } from "../components/Spinner";
import { useFormTutor } from "../tutorial/hooks/useFormTutor";
import { TutorContextualIcon } from "../tutorial/components/TutorContextualIcon";
import { EmitEcfTutorConfig } from "../tutorial/config/emitEcfTutor";

export function EmitECFPage() {
  const { hasPermission } = useAuth();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  
  const tutor = useFormTutor(EmitEcfTutorConfig);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!hasPermission("TENANT_INVOICE_EMIT")) {
      setMessage("No tienes permisos para emitir e-CF.");
      return;
    }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setMessage("e-CF enviado a DGII (simulado).");
    }, 800);
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
                🎓 Iniciar Tutorial
              </button>
            )}
          </h1>
          <p className="text-sm text-slate-300">Firma digitalmente el XML y envíalo a DGII con trazabilidad completa.</p>
          
          {tutor.isActive && (
            <div className="bg-primary/10 border border-primary/30 p-4 rounded-xl mb-4 relative overflow-hidden">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-sm font-bold text-primary mb-1">🤖 {tutor.config.title}</h3>
                  <p className="text-xs text-slate-300 mb-3">{tutor.config.description}</p>
                </div>
                <button onClick={() => tutor.dismissTutor(true)} className="text-xs text-slate-400 hover:text-white underline">Omitir y no volver a mostrar</button>
              </div>
              <p className="text-xs text-primary font-semibold">Pasa el ratón sobre los botones ( ? ) al lado de cada campo para entender su formulación.</p>
            </div>
          )}
        </header>
        <form onSubmit={handleSubmit} className="space-y-6 rounded-xl border border-border bg-slate-900/40 p-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Tipo de Comprobante e-CF */}
            <label className="block space-y-2 text-sm text-foreground" id="tour-step-tipo-ecf">
              <span className="font-semibold text-slate-200 flex items-center">
                Tipo de e-CF <span className="text-red-400 ml-1">*</span>
                {tutor.isActive && tutor.getFieldHelper("tipo-ecf") && <TutorContextualIcon info={tutor.getFieldHelper("tipo-ecf")!} />}
              </span>
              <select className="w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none" required>
                <option value="">Selecciona el tipo de comprobante</option>
                <option value="31">31 - e-CF Factura de Crédito Fiscal</option>
                <option value="32">32 - e-CF Factura de Consumo</option>
                <option value="33">33 - e-CF Nota de Débito</option>
                <option value="34">34 - e-CF Nota de Crédito</option>
              </select>
              <p className="text-xs text-slate-400">Define la serie E del comprobante electrónico.</p>
            </label>

            {/* RNC o Cédula del Comprador */}
            <label className="block space-y-2 text-sm text-foreground" id="tour-step-rnc">
              <span className="font-semibold text-slate-200 flex items-center">
                RNC o Cédula del Comprador <span className="text-red-400 ml-1">*</span>
                {tutor.isActive && tutor.getFieldHelper("comprador-rnc") && <TutorContextualIcon info={tutor.getFieldHelper("comprador-rnc")!} />}
              </span>
              <input type="text" maxLength={11} className="w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none" placeholder="Ej: 101000000" required />
              <p className="text-xs text-slate-400">Debe ser un RNC corporativo válido o cédula dominicana de 11 dígitos.</p>
            </label>
            
            {/* Monto Total y Monto ITBIS */}
            <label className="block space-y-2 text-sm text-foreground" id="tour-step-monto">
              <span className="font-semibold text-slate-200 flex items-center">
                Cobro Total (RD$) <span className="text-red-400 ml-1">*</span>
                {tutor.isActive && tutor.getFieldHelper("total-monto") && <TutorContextualIcon info={tutor.getFieldHelper("total-monto")!} />}
              </span>
              <input type="number" step="0.01" className="w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none" placeholder="0.00" required />
            </label>
            <label className="block space-y-2 text-sm text-foreground" id="tour-step-itbis">
              <span className="font-semibold text-slate-200">ITBIS Facturado (RD$)</span>
              <input type="number" step="0.01" className="w-full rounded-md border border-input bg-slate-950 px-3 py-2 text-sm focus:border-primary focus:outline-none" placeholder="18%" />
            </label>
          </div>

          <label className="block space-y-2 text-sm text-foreground" id="tour-step-payload">
            <span className="font-semibold text-slate-200">Payload XML Restante (o JSON)</span>
            <textarea className="h-32 w-full rounded-md border border-input bg-slate-950 px-3 py-2 font-mono text-xs focus:border-primary focus:outline-none" placeholder="Detalles de items e impuestos adicionales..." />
          </label>

          <label className="flex items-center gap-3 text-sm text-foreground" id="tour-step-sync">
            <input type="checkbox" className="h-4 w-4 rounded border-input bg-slate-950 text-primary accent-primary" defaultChecked />
            <span className="font-semibold text-slate-200 flex items-center">
              Transmisión Ágil (Directa) a DGII
              {tutor.isActive && tutor.getFieldHelper("transmision-agil") && <TutorContextualIcon info={tutor.getFieldHelper("transmision-agil")!} />}
            </span>
          </label>
          
          <div className="flex justify-end pt-4 border-t border-border">
            <button
              id="tour-step-submit"
              className="flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90"
              type="submit"
              disabled={loading}
            >
              {loading ? <Spinner label="Procesando Validación" /> : "Validar y Emitir e-CF"}
            </button>
          </div>
        </form>
        {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      </div>
    </RequirePermission>
  );
}
