import { LeadForm } from "../components/LeadForm";
import { useSite } from "../site-context";

export function ContactPage() {
  const { content } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="max-w-3xl space-y-4">
        <p className="eyebrow">{content.contact.eyebrow}</p>
        <h1 className="display-title">{content.contact.title}</h1>
        <p className="lead-copy">{content.contact.description}</p>
      </header>

      <section className="mt-12 grid gap-6 lg:grid-cols-[0.9fr,1.1fr]">
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.contactChannelsLabel}</h2>
          <ul className="mt-4 space-y-4">
            {content.contact.channels.map((channel) => (
              <li key={channel.label} className="rounded-2xl bg-slate-50 px-5 py-4">
                <p className="text-sm font-semibold text-ink">{channel.label}</p>
                <p className="mt-1 text-sm text-slate-600">{channel.description}</p>
                {channel.href ? (
                  <a className="mt-2 inline-flex text-sm font-semibold text-accent" href={channel.href}>
                    {content.ui.contactOpenLabel}
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
        </article>

        <LeadForm />
      </section>

      <section className="mt-8">
        <article className="surface-card">
          <h2 className="text-xl font-semibold text-ink">{content.ui.contactJourneyLabel}</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {content.contact.journeys.map((journey) => (
              <div key={journey.title} className="rounded-2xl border border-slate-200 px-5 py-4">
                <p className="text-sm font-semibold text-ink">{journey.title}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">{journey.description}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
