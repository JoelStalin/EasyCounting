import { useSite } from "../site-context";

export function EasyCountingPage() {
  const { content, pathFor } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="grid gap-8 lg:grid-cols-[1.15fr,0.85fr] lg:items-end">
        <div className="space-y-4">
          <p className="eyebrow">{content.productDetail.eyebrow}</p>
          <h1 className="display-title">{content.productDetail.title}</h1>
          <p className="lead-copy">{content.productDetail.description}</p>
        </div>
        <div className="surface-card">
          <p className="text-sm font-semibold text-ink">{content.ui.productIncludesLabel}</p>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {content.productDetail.includes.map((feature) => (
              <li key={feature}>• {feature}</li>
            ))}
          </ul>
        </div>
      </header>

      <section className="mt-14 grid gap-6 md:grid-cols-2">
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.productAudienceLabel}</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {content.productDetail.audiences.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.productOutcomesLabel}</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {content.productDetail.outcomes.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="mt-14 rounded-[2rem] bg-ink px-8 py-10 text-white">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-300">{content.ui.productNextStepLabel}</p>
        <h2 className="mt-3 text-3xl font-semibold">{content.ui.productNextStepTitle}</h2>
        <div className="mt-6 flex flex-wrap gap-4">
          <a className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-ink" href="https://cliente.getupsoft.com.do/login">
            {content.ui.productPortalClientLabel}
          </a>
          <a className="rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white" href="https://admin.getupsoft.com.do/login">
            {content.ui.productPortalAdminLabel}
          </a>
          <a className="rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white" href={pathFor("diagnostic")}>
            {content.ui.productDiagnosticCta}
          </a>
        </div>
      </section>
    </div>
  );
}
