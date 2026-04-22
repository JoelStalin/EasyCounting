import { Link } from "react-router-dom";
import { useSite } from "../site-context";

export function ServiceDetailPage({ serviceKey }: { serviceKey: "consulting" | "implementation" | "integrations" | "digitalization" }) {
  const { content, pathFor } = useSite();
  const service = content.serviceDetails[serviceKey];

  return (
    <div className="site-shell py-16">
      <Link className="text-sm font-semibold text-accent" to={pathFor("services")}>
        ← {content.navigation.find((entry) => entry.page === "services")?.label}
      </Link>

      <header className="mt-6 max-w-4xl space-y-4">
        <p className="eyebrow">{service.eyebrow}</p>
        <h1 className="display-title">{service.title}</h1>
        <p className="lead-copy">{service.description}</p>
      </header>

      <section className="mt-12 grid gap-6 lg:grid-cols-3">
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.serviceCapabilitiesLabel}</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {service.capabilities.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.serviceOutcomesLabel}</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {service.outcomes.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.serviceIdealForLabel}</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {service.idealFor.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="mt-10 rounded-[2rem] bg-ink px-8 py-10 text-white">
        <p className="text-sm uppercase tracking-[0.24em] text-slate-300">{service.eyebrow}</p>
        <h2 className="mt-3 text-3xl font-semibold">{service.cta}</h2>
        <div className="mt-6 flex flex-wrap gap-4">
          <Link className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-ink" to={pathFor("diagnostic")}>
            {content.ui.productDiagnosticCta}
          </Link>
          <Link className="rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white" to={pathFor("contact")}>
            {content.navigation.find((entry) => entry.page === "contact")?.label}
          </Link>
        </div>
      </section>
    </div>
  );
}
