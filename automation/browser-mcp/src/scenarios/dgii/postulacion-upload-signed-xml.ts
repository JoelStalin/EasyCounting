import type { ScenarioHandler } from '../../types';
import {
  capturePageState,
  classifyPortalResponse,
  ensureOfvAuthenticated,
  loadCredentials,
  openPostulacionPage,
} from './shared';

export const dgiiPostulacionUploadSignedXmlScenario: ScenarioHandler = async (ctx) => {
  const credentials = loadCredentials(ctx);
  const metadata = ctx.job.target?.metadata || {};
  const signedXmlPath = typeof metadata.signedXmlPath === 'string' ? metadata.signedXmlPath : '';
  if (!signedXmlPath) {
    throw new Error('dgii-postulacion-upload-signed-xml requires target.metadata.signedXmlPath');
  }

  await ensureOfvAuthenticated(ctx, ctx.page, credentials);
  const opened = await openPostulacionPage(ctx, ctx.page, credentials);
  const postulacionPage = opened.page;

  await postulacionPage.locator('#uploadArchivoFirmado').setInputFiles(signedXmlPath);
  await capturePageState(ctx, postulacionPage, 'signed_xml_selected');
  await postulacionPage.locator('#btnEnviarArchivoFirmado').click();
  await postulacionPage.waitForTimeout(8000);
  await postulacionPage.waitForLoadState('domcontentloaded').catch(() => null);
  await capturePageState(ctx, postulacionPage, 'after_signed_upload');

  const bodyPreview = ((await postulacionPage.locator('body').innerText().catch(() => '')) || '').slice(0, 6000);
  const responseClassification = classifyPortalResponse(bodyPreview);
  ctx.recordStep('upload_signed_xml', 'ok', {
    signedXmlPath,
    postulacionUrl: postulacionPage.url(),
    portalAuthResult: opened.portalAuthResult,
  });
  ctx.recordStep(
    'dgii_response_classification',
    responseClassification.classification === 'unknown' ? 'error' : 'ok',
    responseClassification,
  );
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
