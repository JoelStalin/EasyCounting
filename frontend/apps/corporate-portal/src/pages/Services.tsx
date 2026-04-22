import { Link } from "react-router-dom";
import { useSite } from "../site-context";

export function ServicesPage() {
  const { content, pathFor } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="max-w-3xl space-y-4">
        <p className="eyebrow">{content.services.eyebrow}</p>
        <h1 className="display-title">{content.services.title}</h1>
        <p className="lead-copy">{content.services.description}</p>
      </header>

      <section className="mt-12 grid gap-6 lg:grid-cols-2">
        {content.services.items.map((service) => (
          <article key={service.title} className="surface-card">
            <h2 className="text-2xl font-semibold text-ink">{service.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{service.summary}</p>
            <ul className="mt-6 space-y-3 text-sm text-slate-700">
              {service.bullets.map((bullet) => (
                <li key={bullet} className="flex gap-3">
                  <span className="mt-2 h-2 w-2 rounded-full bg-accent" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
            {service.page ? (
              <Link className="mt-6 inline-flex text-sm font-semibold text-accent" to={pathFor(service.page)}>
                {content.ui.serviceViewDetailLabel}
              </Link>
            ) : null}
          </article>
        ))}
      </section>
    </div>
  );
}
