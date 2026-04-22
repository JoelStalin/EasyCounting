import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { DemoStoreNav } from "../components/DemoStoreNav";
import { useDemoCart } from "../hooks/use-demo-cart";

function formatUsd(value: number) {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export function CheckoutPage() {
  const { items, totals, setQuantity, remove, clear } = useDemoCart();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [occasion, setOccasion] = useState("Regalo");
  const [notes, setNotes] = useState("");

  const quoteSummary = useMemo(() => {
    return items.map((item) => `${item.product.name} x${item.quantity} - ${formatUsd(item.subtotalUsd)}`).join("\n");
  }, [items]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const subject = `Solicitud demo Galantes - ${name || "Cliente potencial"}`;
    const body = [
      `Cliente: ${name}`,
      `Correo: ${email}`,
      `Telefono: ${phone}`,
      `Ocasion: ${occasion}`,
      "",
      "Productos:",
      quoteSummary,
      "",
      `Total estimado: ${formatUsd(totals.subtotalUsd)}`,
      "",
      "Notas:",
      notes || "Sin notas adicionales",
    ].join("\n");
    window.location.href = `mailto:info@galantesjewelry.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <DemoStoreNav cartCount={totals.quantity} />
      <main className="mx-auto grid max-w-7xl gap-8 px-4 pb-16 pt-28 sm:px-6 lg:grid-cols-[1fr,0.95fr]">
        <section className="space-y-6">
          <header className="space-y-2">
            <p className="text-sm uppercase tracking-[0.24em] text-amber-200">Checkout demo</p>
            <h1 className="text-3xl font-semibold text-white">Solicitud comercial lista para presentar.</h1>
            <p className="text-sm leading-6 text-slate-300">
              Usa esta vista para mostrar armado de cotizacion, captura de datos y salida comercial por correo.
            </p>
          </header>

          {items.length === 0 ? (
            <div className="rounded-3xl border border-slate-800 bg-slate-900/50 p-8 text-sm text-slate-300">
              Aun no hay productos en la cotizacion.{" "}
              <Link className="font-semibold text-amber-200" to="/catalog">
                Ir al catalogo
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {items.map((item) => (
                <article key={item.product.id} className="flex flex-col gap-4 rounded-3xl border border-slate-800 bg-slate-900/50 p-5 sm:flex-row">
                  <img alt={item.product.name} className="h-28 w-full rounded-2xl object-cover sm:w-32" src={item.product.image} />
                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h2 className="text-lg font-semibold text-white">{item.product.name}</h2>
                        <p className="text-sm text-slate-400">{item.product.description}</p>
                      </div>
                      <span className="text-sm font-semibold text-amber-100">{formatUsd(item.subtotalUsd)}</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                      <label className="text-xs text-slate-400">
                        Cantidad
                        <input
                          className="ml-2 w-20 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
                          min={1}
                          type="number"
                          value={item.quantity}
                          onChange={(event) => setQuantity(item.product.id, Number(event.target.value))}
                        />
                      </label>
                      <button type="button" onClick={() => remove(item.product.id)} className="text-xs font-semibold text-rose-300 hover:text-rose-200">
                        Quitar
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <aside className="space-y-6">
          <section className="rounded-3xl border border-slate-800 bg-slate-900/50 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Resumen</h2>
              <button type="button" onClick={clear} className="text-xs font-semibold text-slate-400 hover:text-white">
                Limpiar
              </button>
            </div>
            <div className="mt-4 space-y-2 text-sm text-slate-300">
              <p>Piezas: <span className="font-semibold text-white">{totals.quantity}</span></p>
              <p>Total estimado: <span className="font-semibold text-amber-100">{formatUsd(totals.subtotalUsd)}</span></p>
            </div>
          </section>

          <form className="space-y-4 rounded-3xl border border-slate-800 bg-slate-900/50 p-6" onSubmit={handleSubmit}>
            <h2 className="text-lg font-semibold text-white">Datos del cliente</h2>
            <input className="w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white" placeholder="Nombre del cliente" value={name} onChange={(event) => setName(event.target.value)} required />
            <input className="w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white" placeholder="Correo" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            <input className="w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white" placeholder="Telefono / WhatsApp" value={phone} onChange={(event) => setPhone(event.target.value)} required />
            <select className="w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white" value={occasion} onChange={(event) => setOccasion(event.target.value)}>
              <option>Regalo</option>
              <option>Compromiso</option>
              <option>Boda</option>
              <option>Coleccion personal</option>
              <option>Compra corporativa</option>
            </select>
            <textarea className="min-h-32 w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white" placeholder="Notas, tallas, presupuesto o referencias." value={notes} onChange={(event) => setNotes(event.target.value)} />
            <button type="submit" disabled={items.length === 0} className="w-full rounded-full bg-amber-200 px-4 py-3 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-300">
              Enviar solicitud comercial
            </button>
          </form>
        </aside>
      </main>
    </div>
  );
}
