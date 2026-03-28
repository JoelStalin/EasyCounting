"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.pdfScreenshotScenario = void 0;
const pdfScreenshotScenario = async (ctx) => {
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
exports.pdfScreenshotScenario = pdfScreenshotScenario;
