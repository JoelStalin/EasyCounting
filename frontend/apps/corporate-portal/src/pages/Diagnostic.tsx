import { LeadForm } from "../components/LeadForm";
import { useSite } from "../site-context";

export function DiagnosticPage() {
  const { content } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="max-w-3xl space-y-4">
        <p className="eyebrow">{content.diagnostic.eyebrow}</p>
        <h1 className="display-title">{content.diagnostic.title}</h1>
        <p className="lead-copy">{content.diagnostic.description}</p>
      </header>

      <section className="mt-12 grid gap-6 lg:grid-cols-2">
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.diagnosticIncludesLabel}</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {content.diagnostic.includes.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.diagnosticQuestionsLabel}</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {content.diagnostic.checkpoints.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="mt-10 rounded-[2rem] bg-ink px-8 py-10 text-white">
        <p className="eyebrow text-slate-300">{content.ui.diagnosticCtaLabel}</p>
        <h2 className="mt-3 text-3xl font-semibold">ventas@getupsoft.com</h2>
        <p className="mt-3 max-w-2xl text-sm text-slate-200">{content.ui.diagnosticCtaDescription}</p>
        <a className="mt-6 inline-flex rounded-full bg-white px-6 py-3 text-sm font-semibold text-ink" href="mailto:ventas@getupsoft.com">
          {content.ui.diagnosticCtaButton}
        </a>
      </section>

      <section className="mt-10">
        <LeadForm defaultInterest={content.contact.journeys[1]?.title} />
      </section>
    </div>
  );
}
