import path from 'node:path';

import type { ScenarioHandler } from '../../types';
import {
  capturePageState,
  ensureOfvAuthenticated,
  loadCredentials,
  openPostulacionPage,
  postulacionFormData,
} from './shared';

export const dgiiPostulacionGenerateXmlScenario: ScenarioHandler = async (ctx) => {
  const credentials = loadCredentials(ctx);
  await ensureOfvAuthenticated(ctx, ctx.page, credentials);
  const opened = await openPostulacionPage(ctx, ctx.page, credentials);
  const postulacionPage = opened.page;

  const fields = postulacionFormData(ctx);
  for (const [id, value] of Object.entries(fields)) {
    const locator = postulacionPage.locator(`#${id}`).first();
    await locator.fill(value);
  }
  await capturePageState(ctx, postulacionPage, 'filled_postulacion');
  const pauseBeforeGenerateSeconds = Number.parseInt(
    String(ctx.job.target?.metadata?.pauseBeforeGenerateSeconds ?? '0'),
    10,
  );
  if (Number.isFinite(pauseBeforeGenerateSeconds) && pauseBeforeGenerateSeconds > 0) {
    await postulacionPage.waitForTimeout(pauseBeforeGenerateSeconds * 1000);
  }

  const downloadPromise = postulacionPage.waitForEvent('download', { timeout: 60000 });
  await postulacionPage.locator('#btnGenerarArchivoValidaciones').first().click();
  const download = await downloadPromise;
  const suggested = download.suggestedFilename() || 'postulacion-validaciones.xml';
  const generatedXmlPath = path.join(ctx.outputDir, suggested);
  await download.saveAs(generatedXmlPath);
  ctx.registerArtifact(generatedXmlPath);
  await capturePageState(ctx, postulacionPage, 'generated_postulacion');
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
