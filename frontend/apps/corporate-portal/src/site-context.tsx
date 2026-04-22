import { createContext, useContext } from "react";
import type { PropsWithChildren } from "react";
import { buildPath, type Locale, type PageKey, SITE_CONTENT } from "./site";

type SiteContextValue = {
  locale: Locale;
  content: (typeof SITE_CONTENT)[Locale];
  pathFor: (page: PageKey, targetLocale?: Locale) => string;
};

const SiteContext = createContext<SiteContextValue | null>(null);

export function SiteProvider({ children, locale }: PropsWithChildren<{ locale: Locale }>) {
  return (
    <SiteContext.Provider
      value={{
        locale,
        content: SITE_CONTENT[locale],
        pathFor: (page, targetLocale = locale) => buildPath(targetLocale, page),
      }}
    >
      {children}
    </SiteContext.Provider>
  );
}

export function useSite() {
  const context = useContext(SiteContext);
  if (!context) {
    throw new Error("useSite must be used inside SiteProvider");
  }
  return context;
}
