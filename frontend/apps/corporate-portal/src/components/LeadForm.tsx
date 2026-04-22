import { useState } from "react";
import { useSite } from "../site-context";

export function LeadForm({ defaultInterest }: { defaultInterest?: string }) {
  const { content } = useSite();
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [interest, setInterest] = useState(defaultInterest ?? content.leadForm.interests[0]);
  const [market, setMarket] = useState(content.leadForm.markets[0]);
  const [challenge, setChallenge] = useState("");

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const subject = `${interest} | ${company || name}`;
    const body = [
      `${content.leadForm.fields.name}: ${name}`,
      `${content.leadForm.fields.company}: ${company}`,
      `${content.leadForm.fields.email}: ${email}`,
      `${content.leadForm.fields.interest}: ${interest}`,
      `${content.leadForm.fields.market}: ${market}`,
      "",
      `${content.leadForm.fields.challenge}:`,
      challenge,
    ].join("\n");

    window.location.href = `mailto:ventas@getupsoft.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  return (
    <form className="surface-card space-y-4" onSubmit={handleSubmit}>
      <div>
        <p className="eyebrow">{content.leadForm.eyebrow}</p>
        <h2 className="mt-3 text-2xl font-semibold text-ink">{content.leadForm.title}</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">{content.leadForm.description}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="space-y-2 text-sm text-slate-700">
          <span>{content.leadForm.fields.name}</span>
          <input className="w-full rounded-xl border border-slate-300 px-4 py-3" value={name} onChange={(event) => setName(event.target.value)} placeholder={content.leadForm.placeholders.name} required />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span>{content.leadForm.fields.company}</span>
          <input className="w-full rounded-xl border border-slate-300 px-4 py-3" value={company} onChange={(event) => setCompany(event.target.value)} placeholder={content.leadForm.placeholders.company} required />
        </label>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="space-y-2 text-sm text-slate-700">
          <span>{content.leadForm.fields.email}</span>
          <input className="w-full rounded-xl border border-slate-300 px-4 py-3" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder={content.leadForm.placeholders.email} required />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span>{content.leadForm.fields.interest}</span>
          <select className="w-full rounded-xl border border-slate-300 px-4 py-3" value={interest} onChange={(event) => setInterest(event.target.value)}>
            {content.leadForm.interests.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="space-y-2 text-sm text-slate-700">
        <span>{content.leadForm.fields.market}</span>
        <select className="w-full rounded-xl border border-slate-300 px-4 py-3" value={market} onChange={(event) => setMarket(event.target.value)}>
          {content.leadForm.markets.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>

      <label className="space-y-2 text-sm text-slate-700">
        <span>{content.leadForm.fields.challenge}</span>
        <textarea className="min-h-36 w-full rounded-xl border border-slate-300 px-4 py-3" value={challenge} onChange={(event) => setChallenge(event.target.value)} placeholder={content.leadForm.placeholders.challenge} required />
      </label>

      <button className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-white hover:bg-accent" type="submit">
        {content.leadForm.submit}
      </button>
    </form>
  );
}
