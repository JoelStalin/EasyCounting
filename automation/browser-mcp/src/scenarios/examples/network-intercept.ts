import type { ScenarioHandler } from '../../types';

export const networkInterceptScenario: ScenarioHandler = async (ctx) => {
  const url = ctx.job.target?.url;
  if (!url) {
    throw new Error('network-intercept requires target.url');
  }
  await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
  await ctx.captureSnapshot('network-intercept');
  ctx.recordStep('network-intercept', 'ok', {
    mockRoutes: ctx.job.networkPolicy?.mockRoutes?.length || 0,
  });
  return {
    mockRoutes: ctx.job.networkPolicy?.mockRoutes?.length || 0,
  };
};
