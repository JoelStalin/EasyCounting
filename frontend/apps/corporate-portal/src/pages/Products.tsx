import { Link } from "react-router-dom";
import { useSite } from "../site-context";

export function ProductsPage() {
  const { content, pathFor } = useSite();

  return (
    <div className="site-shell py-16">
      <header className="max-w-3xl space-y-4">
        <p className="eyebrow">{content.products.eyebrow}</p>
        <h1 className="display-title">{content.products.title}</h1>
        <p className="lead-copy">{content.products.description}</p>
      </header>

      <section className="mt-12 grid gap-6 lg:grid-cols-3">
        {content.products.items.map((product, index) => (
          <article key={product.title} className="surface-card">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent">{product.type}</p>
            <h2 className="mt-3 text-xl font-semibold text-ink">{product.title}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">{product.summary}</p>
            <ul className="mt-5 space-y-2 text-sm text-slate-700">
              {product.bullets.map((bullet) => (
                <li key={bullet}>• {bullet}</li>
              ))}
            </ul>
            {index === 0 ? (
              <Link className="mt-6 inline-flex text-sm font-semibold text-accent" to={pathFor("productDetail")}>
                {content.ui.productsPrimaryCta}
              </Link>
            ) : null}
          </article>
        ))}
      </section>
    </div>
  );
}
