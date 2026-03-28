import type { ScenarioHandler } from '../../types';

export const multiTabScenario: ScenarioHandler = async (ctx) => {
  const metadata = ctx.job.target?.metadata || {};
  const urls = Array.isArray(metadata.urls) ? metadata.urls.map((item) => String(item)) : [];
  if (urls.length === 0) {
    throw new Error('multi-tab requires target.metadata.urls');
  }
  const titles: string[] = [];
  for (const [index, url] of urls.entries()) {
    const page = index === 0 ? ctx.page : await ctx.context.newPage();
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    titles.push(await page.title());
  }
  await ctx.captureScreenshot('multi-tab');
  ctx.recordStep('multi-tab', 'ok', { tabs: urls.length });
  return { titles };
};
