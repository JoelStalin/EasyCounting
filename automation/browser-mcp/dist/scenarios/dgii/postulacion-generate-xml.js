"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.dgiiPostulacionGenerateXmlScenario = void 0;
const node_path_1 = __importDefault(require("node:path"));
const shared_1 = require("./shared");
const dgiiPostulacionGenerateXmlScenario = async (ctx) => {
    const credentials = (0, shared_1.loadCredentials)(ctx);
    await (0, shared_1.ensureOfvAuthenticated)(ctx, ctx.page, credentials);
    const opened = await (0, shared_1.openPostulacionPage)(ctx, ctx.page, credentials);
    const postulacionPage = opened.page;
    const fields = (0, shared_1.postulacionFormData)(ctx);
    for (const [id, value] of Object.entries(fields)) {
        const locator = postulacionPage.locator(`#${id}`).first();
        await locator.fill(value);
    }
    await (0, shared_1.capturePageState)(ctx, postulacionPage, 'filled_postulacion');
    const pauseBeforeGenerateSeconds = Number.parseInt(String(ctx.job.target?.metadata?.pauseBeforeGenerateSeconds ?? '0'), 10);
    if (Number.isFinite(pauseBeforeGenerateSeconds) && pauseBeforeGenerateSeconds > 0) {
        await postulacionPage.waitForTimeout(pauseBeforeGenerateSeconds * 1000);
    }
    const downloadPromise = postulacionPage.waitForEvent('download', { timeout: 60000 });
    await postulacionPage.locator('#btnGenerarArchivoValidaciones').first().click();
    const download = await downloadPromise;
    const suggested = download.suggestedFilename() || 'postulacion-validaciones.xml';
    const generatedXmlPath = node_path_1.default.join(ctx.outputDir, suggested);
    await download.saveAs(generatedXmlPath);
    ctx.registerArtifact(generatedXmlPath);
    await (0, shared_1.capturePageState)(ctx, postulacionPage, 'generated_postulacion');
    ctx.recordStep('form_fill_and_generate', 'ok', {
        generatedXmlPath,
        postulacionUrl: postulacionPage.url(),
        portalAuthResult: opened.portalAuthResult,
    });
    return {
        generatedXmlPath,
        postulacionUrl: postulacionPage.url(),
        softwareName: fields.inputNombreSoftware,
        softwareVersion: fields.inputVersionSoftware,
        authFlow: opened.authFlow,
        portalAuthResult: opened.portalAuthResult,
    };
};
exports.dgiiPostulacionGenerateXmlScenario = dgiiPostulacionGenerateXmlScenario;
