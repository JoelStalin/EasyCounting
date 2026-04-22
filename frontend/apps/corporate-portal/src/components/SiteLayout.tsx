import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useMatches } from "react-router-dom";
import { buildPath, type Locale, type PageKey } from "../site";
import { useSite } from "../site-context";

const BASE_URL = "https://getupsoft.com";
const SOCIAL_IMAGE_URL = `${BASE_URL}/og-default.svg`;
const FAVICON_URL = `${BASE_URL}/favicon.svg`;

function upsertMeta(attr: "name" | "property", key: string, content: string) {
  let element = document.head.querySelector<HTMLMetaElement>(`meta[${attr}="${key}"]`);
  if (!element) {
    element = document.createElement("meta");
    element.setAttribute(attr, key);
    document.head.appendChild(element);
  }
  element.content = content;
}

function upsertLink(rel: string, href: string, hreflang?: string) {
  const selector = hreflang ? `link[rel="${rel}"][hreflang="${hreflang}"]` : `link[rel="${rel}"]`;
  let element = document.head.querySelector<HTMLLinkElement>(selector);
  if (!element) {
    element = document.createElement("link");
    element.rel = rel;
    if (hreflang) {
      element.hreflang = hreflang;
    }
    document.head.appendChild(element);
  }
  element.href = href;
}

function upsertStructuredData(scriptId: string, payload: Record<string, unknown>) {
  let element = document.head.querySelector<HTMLScriptElement>(`script[data-seo="${scriptId}"]`);
  if (!element) {
    element = document.createElement("script");
    element.type = "application/ld+json";
    element.dataset.seo = scriptId;
    document.head.appendChild(element);
  }
  element.textContent = JSON.stringify(payload);
}

export function SiteLayout() {
  const { locale, content, pathFor } = useSite();
  const location = useLocation();
  const matches = useMatches();
  const [showSuggestion, setShowSuggestion] = useState(false);
  const currentPage = useMemo(() => {
    const matched = [...matches]
      .reverse()
      .find((entry) => typeof entry.handle === "object" && entry.handle && "pageKey" in entry.handle) as
      | { handle: { pageKey: PageKey } }
      | undefined;
    return matched?.handle.pageKey ?? "home";
  }, [matches]);

  const alternateLocale: Locale = locale === "es" ? "en" : "es";

  useEffect(() => {
    const browserPrefersEnglish = navigator.language.toLowerCase().startsWith("en");
    const savedLocale = window.localStorage.getItem("getupsoft-locale");
    setShowSuggestion(locale === "es" && location.pathname === "/" && !savedLocale && browserPrefersEnglish);
  }, [locale, location.pathname]);

  useEffect(() => {
    window.localStorage.setItem("getupsoft-locale", locale);
    document.documentElement.lang = locale === "es" ? "es-DO" : "en-US";

    const meta = content.meta[currentPage];
    const canonicalUrl = `${BASE_URL}${buildPath(locale, currentPage)}`;
    const socialType = currentPage === "productDetail" ? "product" : currentPage.startsWith("case") ? "article" : "website";

    document.title = meta.title;
    upsertMeta("name", "description", meta.description);
    upsertMeta("name", "robots", "index,follow");
    upsertMeta("property", "og:title", meta.title);
    upsertMeta("property", "og:description", meta.description);
    upsertMeta("property", "og:url", canonicalUrl);
    upsertMeta("property", "og:type", socialType);
    upsertMeta("property", "og:site_name", "GetUpSoft");
    upsertMeta("property", "og:locale", locale === "es" ? "es_DO" : "en_US");
    upsertMeta("property", "og:image", SOCIAL_IMAGE_URL);
    upsertMeta("property", "og:image:secure_url", SOCIAL_IMAGE_URL);
    upsertMeta("property", "og:image:type", "image/svg+xml");
    upsertMeta("property", "og:image:width", "1200");
    upsertMeta("property", "og:image:height", "630");

    upsertLink("canonical", canonicalUrl);
    upsertLink("alternate", `${BASE_URL}${buildPath("es", currentPage)}`, "es-DO");
    upsertLink("alternate", `${BASE_URL}${buildPath("en", currentPage)}`, "en-US");
    upsertLink("alternate", `${BASE_URL}${buildPath("es", currentPage)}`, "x-default");
    upsertLink("icon", FAVICON_URL);

    upsertStructuredData("organization", {
      "@context": "https://schema.org",
      "@type": "Organization",
      name: "GetUpSoft",
      url: BASE_URL,
      logo: FAVICON_URL,
      email: "ventas@getupsoft.com",
      description: content.meta.home.description,
      knowsAbout: [
        "Digital transformation consulting",
        "Technology implementation",
        "Systems integration",
        "Automation",
        "Operational support",
        "EasyCounting",
      ],
    });

    upsertStructuredData("webpage", {
      "@context": "https://schema.org",
      "@type": "WebPage",
      name: meta.title,
      description: meta.description,
      inLanguage: locale === "es" ? "es-DO" : "en-US",
      url: canonicalUrl,
      isPartOf: {
        "@type": "WebSite",
        name: "GetUpSoft",
        url: BASE_URL,
      },
      about: {
        "@type": "Organization",
        name: "GetUpSoft",
      },
    });
  }, [content.meta, currentPage, locale]);

  return (
    <div className="min-h-screen">
      {showSuggestion ? (
        <div className="border-b border-accent/20 bg-accent/10 px-4 py-3 text-center text-sm text-slate-700">
          {content.ui.languageSuggestion}{" "}
          <Link className="font-semibold text-accent" to={pathFor(currentPage, alternateLocale)} onClick={() => setShowSuggestion(false)}>
            {content.ui.languageSuggestionAction}
          </Link>
        </div>
      ) : null}

      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-sand/90 backdrop-blur">
        <div className="site-shell flex flex-col gap-5 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <Link to={pathFor("home")} className="text-xs uppercase tracking-[0.28em] text-slate-500">
              GetUpSoft
            </Link>
            <p className="text-lg font-semibold text-ink">{content.ui.headerTagline}</p>
          </div>

          <nav className="flex flex-wrap gap-4 text-sm font-medium text-slate-700 lg:justify-center">
            {content.navigation.map((item) => (
              <NavLink
                key={item.page}
                to={pathFor(item.page)}
                className={({ isActive }) => (isActive ? "text-accent" : "hover:text-accent")}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              className="rounded-full border border-slate-300 px-4 py-2 text-sm hover:border-accent hover:text-accent"
              to={pathFor(currentPage, alternateLocale)}
            >
              {content.switchLabel}
            </Link>
            <a className="rounded-full border border-slate-300 px-4 py-2 text-sm hover:border-accent hover:text-accent" href="https://admin.getupsoft.com.do/login">
              Admin
            </a>
            <a className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-accent" href="https://easycounting.getupsoft.com">
              EasyCounting
            </a>
          </div>
        </div>
      </header>

      <main>
        <Outlet />
      </main>

      <footer className="border-t border-slate-200/80 bg-white/80">
        <div className="site-shell grid gap-8 py-12 md:grid-cols-[1.3fr,1fr,1fr,1fr]">
          <div>
            <p className="text-sm font-semibold text-ink">GetUpSoft</p>
            <p className="mt-3 text-sm leading-6 text-slate-600">{content.footer.description}</p>
          </div>
          {content.footer.columns.map((column) => (
            <div key={column.title}>
              <p className="text-sm font-semibold text-ink">{column.title}</p>
              <ul className="mt-3 space-y-2 text-sm text-slate-600">
                {column.links.map((link) => (
                  <li key={link.label}>
                    {link.page ? (
                      <Link to={pathFor(link.page)} className="hover:text-accent">
                        {link.label}
                      </Link>
                    ) : link.href ? (
                      <a href={link.href} className="hover:text-accent">
                        {link.label}
                      </a>
                    ) : (
                      <span>{link.label}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </footer>
    </div>
  );
}
