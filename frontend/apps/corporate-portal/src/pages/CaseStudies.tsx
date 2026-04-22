import { Link } from "react-router-dom";
import { useSite } from "../site-context";

export function CaseStudiesPage() {
  const { content, pathFor } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="max-w-4xl space-y-4">
        <p className="eyebrow">{content.cases.eyebrow}</p>
        <h1 className="display-title">{content.cases.title}</h1>
        <p className="lead-copy">{content.cases.description}</p>
      </header>

      <section className="mt-12 grid gap-6 xl:grid-cols-2">
        {content.cases.items.map((item) => {
          const detailPage = item.id === "galantes" ? "caseGalantes" : "caseChefalitas";
          return (
            <article key={item.client} className="surface-card">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent">{item.industry}</p>
              <h2 className="mt-3 text-2xl font-semibold text-ink">{item.client}</h2>
              <p className="mt-2 text-lg text-slate-700">{item.headline}</p>
              <p className="mt-4 text-sm leading-6 text-slate-600">{item.summary}</p>
              <p className="mt-5 text-sm font-semibold text-ink">{content.ui.casesChallengeLabel}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{item.challenge}</p>
              <p className="mt-5 text-sm font-semibold text-ink">{content.ui.casesInterventionLabel}</p>
              <ul className="mt-2 space-y-2 text-sm text-slate-600">
                {item.intervention.map((step) => (
                  <li key={step}>• {step}</li>
                ))}
              </ul>
              <Link className="mt-6 inline-flex text-sm font-semibold text-accent" to={pathFor(detailPage)}>
                {content.ui.casesReadMoreLabel}
              </Link>
            </article>
          );
        })}
      </section>
    </div>
  );
}
