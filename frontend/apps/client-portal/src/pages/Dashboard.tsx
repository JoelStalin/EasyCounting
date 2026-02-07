import { FileText, ScanBarcode, ShieldCheck } from "lucide-react";
import { CardKPI } from "../components/CardKPI";

const KPIS = [
  {
    title: "Comprobantes emitidos",
    value: "1,245",
    subtitle: "Últimos 30 días",
    icon: <FileText className="h-5 w-5 text-primary" aria-hidden />,
  },
  {
    title: "RFCE enviados",
    value: "842",
    subtitle: "Procesados en modo resumen",
    icon: <ShieldCheck className="h-5 w-5 text-primary" aria-hidden />,
  },
  {
    title: "RI descargadas",
    value: "692",
    subtitle: "Con QR y hash de seguridad",
    icon: <ScanBarcode className="h-5 w-5 text-primary" aria-hidden />,
  },
];

export function DashboardPage() {
  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-white">Resumen del tenant</h1>
        <p className="text-sm text-slate-300">
          Seguimiento operativo de envíos DGII, planes tarifarios y controles de aprobación.
        </p>
      </header>
      <section className="grid gap-4 md:grid-cols-3">
        {KPIS.map((kpi) => (
          <CardKPI key={kpi.title} {...kpi} />
        ))}
      </section>
      <section className="space-y-3 text-sm text-slate-300">
        <h2 className="text-lg font-semibold text-white">Próximas acciones</h2>
        <ul className="space-y-2">
          <li>• Subir nuevo certificado .p12 antes de que expire el actual.</li>
          <li>• Revisar aprobaciones comerciales pendientes (ACECF).</li>
          <li>• Ejecutar conciliación con Odoo para facturas del mes.</li>
        </ul>
      </section>
    </div>
  );
}
