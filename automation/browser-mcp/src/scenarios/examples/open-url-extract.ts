import type { ScenarioHandler } from '../../types';

export const openUrlExtractScenario: ScenarioHandler = async (ctx) => {
  const url = ctx.job.target?.url;
  if (!url) {
    throw new Error('open-url-extract requires target.url');
  }
  await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
  await ctx.captureSnapshot('landing');
  await ctx.captureScreenshot('landing');
  const title = await ctx.page.title();
  const heading = await ctx.page.locator('h1').first().textContent().catch(() => null);
  ctx.recordStep('open-url', 'ok', { url, title });
  return {
    url,
    title,
    heading,
  };
};
