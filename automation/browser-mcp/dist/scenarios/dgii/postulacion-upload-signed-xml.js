"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.dgiiPostulacionUploadSignedXmlScenario = void 0;
const shared_1 = require("./shared");
const dgiiPostulacionUploadSignedXmlScenario = async (ctx) => {
    const credentials = (0, shared_1.loadCredentials)(ctx);
    const metadata = ctx.job.target?.metadata || {};
    const signedXmlPath = typeof metadata.signedXmlPath === 'string' ? metadata.signedXmlPath : '';
    if (!signedXmlPath) {
        throw new Error('dgii-postulacion-upload-signed-xml requires target.metadata.signedXmlPath');
    }
    await (0, shared_1.ensureOfvAuthenticated)(ctx, ctx.page, credentials);
    const opened = await (0, shared_1.openPostulacionPage)(ctx, ctx.page, credentials);
    const postulacionPage = opened.page;
    await postulacionPage.locator('#uploadArchivoFirmado').setInputFiles(signedXmlPath);
    await (0, shared_1.capturePageState)(ctx, postulacionPage, 'signed_xml_selected');
    await postulacionPage.locator('#btnEnviarArchivoFirmado').click();
    await postulacionPage.waitForTimeout(8000);
    await postulacionPage.waitForLoadState('domcontentloaded').catch(() => null);
    await (0, shared_1.capturePageState)(ctx, postulacionPage, 'after_signed_upload');
    const bodyPreview = ((await postulacionPage.locator('body').innerText().catch(() => '')) || '').slice(0, 6000);
    const responseClassification = (0, shared_1.classifyPortalResponse)(bodyPreview);
    ctx.recordStep('upload_signed_xml', 'ok', {
        signedXmlPath,
        postulacionUrl: postulacionPage.url(),
        portalAuthResult: opened.portalAuthResult,
    });
    ctx.recordStep('dgii_response_classification', responseClassification.classification === 'unknown' ? 'error' : 'ok', responseClassification);
    return {
        signedXmlPath,
        postulacionUrl: postulacionPage.url(),
        title: await postulacionPage.title(),
        bodyPreview,
        authFlow: opened.authFlow,
        portalAuthResult: opened.portalAuthResult,
        responseClassification,
    };
};
exports.dgiiPostulacionUploadSignedXmlScenario = dgiiPostulacionUploadSignedXmlScenario;
