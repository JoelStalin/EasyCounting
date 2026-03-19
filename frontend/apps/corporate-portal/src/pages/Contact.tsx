export function ContactPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <header className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Contacto</p>
        <h1 className="text-4xl font-semibold text-ink">Coordina una demo comercial o tecnica.</h1>
        <p className="text-lg text-slate-600">
          Para prospectos, integradores y partners que necesitan una revision guiada del producto y sus portales.
        </p>
      </header>
      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6">
          <h2 className="text-xl font-semibold text-ink">Accesos directos</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li><a href="https://admin.getupsoft.com.do/login">Portal Admin</a></li>
            <li><a href="https://cliente.getupsoft.com.do/login">Portal Cliente</a></li>
            <li><a href="https://socios.getupsoft.com.do/login">Portal Socios</a></li>
          </ul>
        </article>
        <article className="rounded-[1.75rem] border border-slate-200 bg-white/90 p-6">
          <h2 className="text-xl font-semibold text-ink">Canal sugerido</h2>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Usa el portal cliente para la demo funcional y el portal admin para la demostracion de gobierno, planes y proveedores IA.
          </p>
        </article>
      </div>
    </div>
  );
}
