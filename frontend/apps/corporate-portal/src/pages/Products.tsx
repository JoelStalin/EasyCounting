import { Link } from "react-router-dom";

const products = [
  {
    name: "Accounting Management",
    description: "Gestion contable y cumplimiento fiscal para empresas que necesitan control, reporteria y operacion diaria integrada.",
    href: "/productos/accounting-management",
  },
  {
    name: "Portal Cliente",
    description: "Emision, seguimiento de comprobantes, certificados y asistente sobre facturas del propio tenant.",
    href: "https://cliente.getupsoft.com.do/login",
  },
  {
    name: "Portal Socios",
    description: "Canal de revendedores con cartera asignada, permisos diferenciados y emision demo controlada.",
    href: "https://socios.getupsoft.com.do/login",
  },
];

export function ProductsPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-16">
      <header className="max-w-3xl space-y-4">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Productos</p>
        <h1 className="text-4xl font-semibold text-ink">Un stack operativo para cumplimiento y crecimiento.</h1>
        <p className="text-lg text-slate-600">
          La suite GetUpSoft combina administracion multi-tenant, operacion comercial y gestion contable orientada a e-CF.
        </p>
      </header>
      <div className="mt-10 grid gap-6 md:grid-cols-3">
        {products.map((product) => (
          <article key={product.name} className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-ink">{product.name}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{product.description}</p>
            {product.href.startsWith("/") ? (
              <Link className="mt-6 inline-flex text-sm font-semibold text-accent" to={product.href}>
                Ver detalle
              </Link>
            ) : (
              <a className="mt-6 inline-flex text-sm font-semibold text-accent" href={product.href}>
                Abrir portal
              </a>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
