import { useSite } from "../site-context";

export function CompanyPage() {
  const { content } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="max-w-3xl space-y-4">
        <p className="eyebrow">{content.company.eyebrow}</p>
        <h1 className="display-title">{content.company.title}</h1>
        <p className="lead-copy">{content.company.description}</p>
      </header>

      <section className="mt-12 grid gap-6 md:grid-cols-3">
        {content.company.pillars.map((pillar) => (
          <article key={pillar.title} className="surface-card">
            <h2 className="text-xl font-semibold text-ink">{pillar.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{pillar.description}</p>
          </article>
        ))}
      </section>

      <section className="mt-12 rounded-[2rem] border border-slate-200 bg-white/90 p-8">
        <p className="eyebrow">{content.ui.companyPrinciplesLabel}</p>
        <ul className="mt-4 grid gap-4 md:grid-cols-3">
          {content.company.principles.map((principle) => (
            <li key={principle} className="rounded-2xl bg-slate-50 px-5 py-4 text-sm text-slate-700">
              {principle}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
