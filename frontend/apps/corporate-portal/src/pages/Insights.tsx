import { useSite } from "../site-context";

export function InsightsPage() {
  const { content } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="max-w-3xl space-y-4">
        <p className="eyebrow">{content.insights.eyebrow}</p>
        <h1 className="display-title">{content.insights.title}</h1>
        <p className="lead-copy">{content.insights.description}</p>
      </header>

      <section className="mt-12 grid gap-6 md:grid-cols-3">
        {content.insights.pillars.map((pillar) => (
          <article key={pillar.title} className="surface-card">
            <h2 className="text-xl font-semibold text-ink">{pillar.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{pillar.summary}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
