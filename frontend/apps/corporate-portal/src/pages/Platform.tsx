import { useSite } from "../site-context";

export function SolutionsPage() {
  const { content } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="max-w-3xl space-y-4">
        <p className="eyebrow">{content.solutions.eyebrow}</p>
        <h1 className="display-title">{content.solutions.title}</h1>
        <p className="lead-copy">{content.solutions.description}</p>
      </header>
      <section className="mt-12 grid gap-6 lg:grid-cols-3">
        {content.solutions.segments.map((segment) => (
          <article key={segment.title} className="surface-card">
            <h2 className="text-xl font-semibold text-ink">{segment.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{segment.summary}</p>
            <ul className="mt-5 space-y-2 text-sm text-slate-700">
              {segment.bullets.map((bullet) => (
                <li key={bullet}>• {bullet}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>
    </div>
  );
}
