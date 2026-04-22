import { Link } from "react-router-dom";
import { useSite } from "../site-context";

export function CaseStudyDetailPage({ caseId }: { caseId: "galantes" | "chefalitas" }) {
  const { content, pathFor } = useSite();
  const item = content.cases.items.find((entry) => entry.id === caseId);

  if (!item) {
    return null;
  }

  return (
    <div className="site-shell py-16">
      <Link className="text-sm font-semibold text-accent" to={pathFor("cases")}>
        ← {content.navigation.find((entry) => entry.page === "cases")?.label}
      </Link>

      <header className="mt-6 max-w-4xl space-y-4">
        <p className="eyebrow">{item.industry}</p>
        <h1 className="display-title">{item.client}</h1>
        <p className="lead-copy">{item.headline}</p>
        <p className="text-base leading-7 text-slate-600">{item.summary}</p>
      </header>

      <section className="mt-12 grid gap-6 lg:grid-cols-[0.9fr,1.1fr]">
        <article className="surface-card">
          <p className="text-sm font-semibold text-ink">{content.ui.caseContextLabel}</p>
          <p className="mt-3 text-sm leading-6 text-slate-600">{item.challenge}</p>
          <p className="mt-5 text-sm font-semibold text-ink">{content.ui.caseEvidenceLabel}</p>
          <p className="mt-3 text-sm leading-6 text-slate-600">{item.evidence}</p>
        </article>

        <article className="surface-card">
          <p className="text-sm font-semibold text-ink">{content.ui.caseInterventionDetailLabel}</p>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {item.intervention.map((step) => (
              <li key={step}>• {step}</li>
            ))}
          </ul>
          <p className="mt-6 text-sm font-semibold text-ink">{content.ui.caseOutcomeLabel}</p>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {item.outcome.map((outcome) => (
              <li key={outcome}>• {outcome}</li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}
