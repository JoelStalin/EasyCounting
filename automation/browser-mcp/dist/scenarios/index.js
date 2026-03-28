"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.scenarioRegistry = void 0;
exports.getScenario = getScenario;
const cookies_localstorage_1 = require("./examples/cookies-localstorage");
const download_evidence_1 = require("./examples/download-evidence");
const form_fill_1 = require("./examples/form-fill");
const login_persistent_session_1 = require("./examples/login-persistent-session");
const multi_tab_1 = require("./examples/multi-tab");
const network_intercept_1 = require("./examples/network-intercept");
const open_url_extract_1 = require("./examples/open-url-extract");
const pdf_screenshot_1 = require("./examples/pdf-screenshot");
const ofv_login_1 = require("./dgii/ofv-login");
const postulacion_generate_xml_1 = require("./dgii/postulacion-generate-xml");
const postulacion_open_1 = require("./dgii/postulacion-open");
const postulacion_upload_signed_xml_1 = require("./dgii/postulacion-upload-signed-xml");
const login_1 = require("./odoo/login");
exports.scenarioRegistry = {
    'open-url-extract': open_url_extract_1.openUrlExtractScenario,
    'login-persistent-session': login_persistent_session_1.loginPersistentSessionScenario,
    'form-fill': form_fill_1.formFillScenario,
    'download-evidence': download_evidence_1.downloadEvidenceScenario,
    'cookies-localstorage': cookies_localstorage_1.cookiesLocalstorageScenario,
    'network-intercept': network_intercept_1.networkInterceptScenario,
    'pdf-screenshot': pdf_screenshot_1.pdfScreenshotScenario,
    'multi-tab': multi_tab_1.multiTabScenario,
    'dgii-ofv-login': ofv_login_1.dgiiOfvLoginScenario,
    'dgii-postulacion-open': postulacion_open_1.dgiiPostulacionOpenScenario,
    'dgii-postulacion-generate-xml': postulacion_generate_xml_1.dgiiPostulacionGenerateXmlScenario,
    'dgii-postulacion-upload-signed-xml': postulacion_upload_signed_xml_1.dgiiPostulacionUploadSignedXmlScenario,
    'odoo-login': login_1.odooLoginScenario,
};
function getScenario(name) {
    const scenario = exports.scenarioRegistry[name];
    if (!scenario) {
        throw new Error(`Unknown scenario: ${name}`);
    }
    return scenario;
}
