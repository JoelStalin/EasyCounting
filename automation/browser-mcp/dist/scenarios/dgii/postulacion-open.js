"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.dgiiPostulacionOpenScenario = void 0;
const dgiiPostulacionOpenScenario = async (ctx) => {
    const url = ctx.job.target?.url || 'https://dgii.gov.do/OFV/FacturaElectronica/FE_Facturador_Electronico.aspx';
    await ctx.page.goto(url, { waitUntil: 'domcontentloaded' });
    await ctx.captureSnapshot('dgii-postulacion');
    await ctx.captureScreenshot('dgii-postulacion');
    ctx.recordStep('dgii-postulacion-open', 'ok', { url });
    return { url };
};
exports.dgiiPostulacionOpenScenario = dgiiPostulacionOpenScenario;
