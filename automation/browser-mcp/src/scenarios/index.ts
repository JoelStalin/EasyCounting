import { cookiesLocalstorageScenario } from './examples/cookies-localstorage';
import { downloadEvidenceScenario } from './examples/download-evidence';
import { formFillScenario } from './examples/form-fill';
import { loginPersistentSessionScenario } from './examples/login-persistent-session';
import { multiTabScenario } from './examples/multi-tab';
import { networkInterceptScenario } from './examples/network-intercept';
import { openUrlExtractScenario } from './examples/open-url-extract';
import { pdfScreenshotScenario } from './examples/pdf-screenshot';
import { dgiiOfvLoginScenario } from './dgii/ofv-login';
import { dgiiPostulacionGenerateXmlScenario } from './dgii/postulacion-generate-xml';
import { dgiiPostulacionOpenScenario } from './dgii/postulacion-open';
import { dgiiPostulacionUploadSignedXmlScenario } from './dgii/postulacion-upload-signed-xml';
import { odooLoginScenario } from './odoo/login';
import type { ScenarioHandler } from '../types';

export const scenarioRegistry: Record<string, ScenarioHandler> = {
  'open-url-extract': openUrlExtractScenario,
  'login-persistent-session': loginPersistentSessionScenario,
  'form-fill': formFillScenario,
  'download-evidence': downloadEvidenceScenario,
  'cookies-localstorage': cookiesLocalstorageScenario,
  'network-intercept': networkInterceptScenario,
  'pdf-screenshot': pdfScreenshotScenario,
  'multi-tab': multiTabScenario,
  'dgii-ofv-login': dgiiOfvLoginScenario,
  'dgii-postulacion-open': dgiiPostulacionOpenScenario,
  'dgii-postulacion-generate-xml': dgiiPostulacionGenerateXmlScenario,
  'dgii-postulacion-upload-signed-xml': dgiiPostulacionUploadSignedXmlScenario,
  'odoo-login': odooLoginScenario,
};

export function getScenario(name: string): ScenarioHandler {
  const scenario = scenarioRegistry[name];
  if (!scenario) {
    throw new Error(`Unknown scenario: ${name}`);
  }
  return scenario;
}
