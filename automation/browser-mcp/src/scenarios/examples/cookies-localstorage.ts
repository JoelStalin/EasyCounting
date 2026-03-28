import type { ScenarioHandler } from '../../types';

export const cookiesLocalstorageScenario: ScenarioHandler = async (ctx) => {
  const url = ctx.job.target?.url;
  const metadata = ctx.job.target?.metadata || {};
  const cookies = Array.isArray(metadata.cookies) ? metadata.cookies : [];
  const storageEntries =
    metadata.localStorage && typeof metadata.localStorage === 'object'
      ? (metadata.localStorage as Record<string, string>)
      : {};

  if (!url) {
    throw new Error('cookies-localstorage requires target.url');
  }

  if (cookies.length > 0) {
    await ctx.context.addCookies(cookies as Parameters<typeof ctx.context.addCookies>[0]);
  }
  await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
  await ctx.page.evaluate((entries) => {
    Object.entries(entries).forEach(([key, value]) => window.localStorage.setItem(key, value));
  }, storageEntries);
  const loaded = await ctx.page.evaluate(() => ({
    localStorage: { ...window.localStorage },
    cookies: document.cookie,
  }));
  await ctx.captureSnapshot('cookies-localstorage');
  ctx.recordStep('cookies-localstorage', 'ok', { cookieCount: cookies.length });
  return loaded;
};
