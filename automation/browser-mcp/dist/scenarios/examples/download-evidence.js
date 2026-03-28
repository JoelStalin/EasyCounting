"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.downloadEvidenceScenario = void 0;
const downloadEvidenceScenario = async (ctx) => {
    const url = ctx.job.target?.url;
    if (!url) {
        throw new Error('download-evidence requires target.url');
    }
    await ctx.page.goto(url, { waitUntil: 'networkidle' });
    const html = await ctx.page.content();
    const htmlPath = await ctx.writeArtifact('page.html', html);
    const screenshotPath = await ctx.captureScreenshot('evidence');
    const pdfPath = await ctx.capturePdf('evidence');
    ctx.recordStep('download-evidence', 'ok', { url, htmlPath, screenshotPath, pdfPath });
    return { htmlPath, screenshotPath, pdfPath };
};
exports.downloadEvidenceScenario = downloadEvidenceScenario;
