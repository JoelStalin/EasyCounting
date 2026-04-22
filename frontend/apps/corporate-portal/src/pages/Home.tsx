import { Link } from "react-router-dom";
import { useSite } from "../site-context";

export function HomePage() {
  const { content, pathFor } = useSite();

  return (
    <div className="site-shell py-14">
      <section className="grid gap-10 lg:grid-cols-[1.1fr,0.9fr] lg:items-center">
        <div className="space-y-6">
          <span className="inline-flex rounded-full border border-accent/25 bg-accent/10 px-4 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-accent">
            {content.hero.eyebrow}
          </span>
          <div className="space-y-4">
            <h1 className="max-w-4xl text-5xl font-semibold leading-tight text-ink">{content.hero.title}</h1>
            <p className="max-w-3xl text-lg text-slate-600">{content.hero.description}</p>
          </div>
          <div className="flex flex-wrap gap-4">
            <Link className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-white hover:bg-accent" to={pathFor("diagnostic")}>
              {content.hero.primaryCta}
            </Link>
            <Link className="rounded-full border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-800 hover:border-accent hover:text-accent" to={pathFor("cases")}>
              {content.hero.secondaryCta}
            </Link>
          </div>
        </div>

        <div className="grid gap-4 rounded-[2rem] border border-slate-200 bg-white/90 p-8 shadow-[0_30px_90px_rgba(15,23,42,0.08)]">
          {content.homeStats.map((metric) => (
            <div key={metric.label} className="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">{metric.label}</p>
              <p className="mt-2 text-xl font-semibold text-ink">{metric.value}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-16 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {content.homeTrust.map((item) => (
          <article key={item} className="rounded-[1.75rem] border border-slate-200 bg-white/85 p-6">
            <p className="text-sm font-semibold text-ink">{item}</p>
          </article>
        ))}
      </section>

      <section className="mt-16 grid gap-6 lg:grid-cols-[1fr,1fr]">
        <article className="surface-card">
          <p className="eyebrow">{content.products.eyebrow}</p>
          <h2 className="mt-3 text-3xl font-semibold text-ink">{content.products.title}</h2>
          <p className="mt-4 text-sm leading-6 text-slate-600">{content.products.description}</p>
          <Link className="mt-6 inline-flex text-sm font-semibold text-accent" to={pathFor("products")}>
            {content.ui.homeProductsCta}
          </Link>
        </article>
        <article className="surface-card">
          <p className="eyebrow">{content.cases.eyebrow}</p>
          <h2 className="mt-3 text-3xl font-semibold text-ink">{content.cases.title}</h2>
          <p className="mt-4 text-sm leading-6 text-slate-600">{content.cases.description}</p>
          <div className="mt-5 space-y-3">
            {content.cases.items.map((item) => (
              <div key={item.client} className="rounded-2xl bg-slate-50 px-5 py-4">
                <p className="text-sm font-semibold text-ink">{item.client}</p>
                <p className="mt-1 text-sm text-slate-600">{item.summary}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
