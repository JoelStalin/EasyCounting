import type { ScenarioHandler } from '../../types';

export const pdfScreenshotScenario: ScenarioHandler = async (ctx) => {
  const url = ctx.job.target?.url;
  if (!url) {
    throw new Error('pdf-screenshot requires target.url');
  }
  await ctx.page.goto(url, { waitUntil: 'networkidle' });
  const screenshotPath = await ctx.captureScreenshot('page');
  const pdfPath = await ctx.capturePdf('page');
  ctx.recordStep('pdf-screenshot', 'ok', { screenshotPath, pdfPath });
  return { screenshotPath, pdfPath };
};
