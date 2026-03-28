"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.networkInterceptScenario = void 0;
const networkInterceptScenario = async (ctx) => {
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
exports.networkInterceptScenario = networkInterceptScenario;
