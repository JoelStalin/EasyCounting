import { Link } from "react-router-dom";
import { DemoStoreNav } from "../components/DemoStoreNav";
import { useDemoCart } from "../hooks/use-demo-cart";

function formatUsd(value: number) {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export function CatalogPage() {
  const { catalog, totals, add } = useDemoCart();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <DemoStoreNav cartCount={totals.quantity} />
      <main className="mx-auto max-w-7xl px-4 pb-16 pt-28 sm:px-6">
        <section className="grid gap-8 rounded-3xl border border-amber-200/10 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 px-6 py-10 lg:grid-cols-[1.2fr,0.8fr]">
          <div className="space-y-4">
            <p className="text-sm uppercase tracking-[0.24em] text-amber-200">Galante's Jewelry Demo</p>
            <h1 className="text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              Catalogo de muestra listo para ventas, cotizacion y onboarding comercial.
            </h1>
            <p className="max-w-2xl text-sm leading-7 text-slate-300">
              Este flujo permite mostrar 10 piezas con imagen, precio estimado y construccion de solicitud comercial
              para validar la conversacion con el cliente.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link className="rounded-full bg-amber-200 px-5 py-3 text-sm font-semibold text-slate-950" to="/checkout">
                Ver cotizacion
              </Link>
              <Link className="rounded-full border border-slate-700 px-5 py-3 text-sm font-semibold text-white" to="/login">
                Acceso clientes
              </Link>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Piezas demo</p>
              <p className="mt-3 text-3xl font-semibold text-white">10</p>
              <p className="mt-2 text-sm text-slate-400">Muestra comercial lista para presentar.</p>
            </div>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
              <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Ticket estimado</p>
              <p className="mt-3 text-3xl font-semibold text-white">{formatUsd(1125)}</p>
              <p className="mt-2 text-sm text-slate-400">Promedio demo de venta premium.</p>
            </div>
          </div>
        </section>

        <section className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {catalog.map((product) => (
            <article key={product.id} className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/50">
              <img alt={product.name} className="h-72 w-full object-cover" src={product.image} />
              <div className="space-y-4 p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.2em] text-amber-200">{product.category}</p>
                    <h2 className="mt-2 text-xl font-semibold text-white">{product.name}</h2>
                  </div>
                  <span className="rounded-full border border-amber-200/30 bg-amber-200/10 px-3 py-1 text-sm font-semibold text-amber-100">
                    {formatUsd(product.priceUsd)}
                  </span>
                </div>
                <p className="text-sm leading-6 text-slate-300">{product.description}</p>
                <ul className="space-y-2 text-xs text-slate-400">
                  {product.highlights.map((highlight) => (
                    <li key={highlight}>• {highlight}</li>
                  ))}
                </ul>
                <button
                  type="button"
                  onClick={() => add(product.id)}
                  className="w-full rounded-full bg-white px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-amber-100"
                >
                  Agregar a cotizacion
                </button>
              </div>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
