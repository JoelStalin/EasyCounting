import { FormTutorialConfig } from "../types";

export const EmitEcfTutorConfig: FormTutorialConfig = {
  formId: "emit-ecf-form",
  title: "Guía de Emisión de e-CF",
  description: "Aprende a parametrizar correctamente un Comprobante Fiscal Electrónico ante la DGII.",
  fields: {
    "tipo-ecf": {
      fieldId: "tipo-ecf",
      label: "Tipo de e-CF",
      description: "Define la naturaleza fiscal del comprobante, indispensable para el reporte de impuestos de tu cliente.",
      expectedFormat: "Selección de lista (31 al 45)",
      exampleValue: "31 - Factura de Crédito Fiscal",
      isRequired: true,
      businessImpact: "Si eliges '31' pero tu cliente no reporta ITBIS o no tiene RNC registrado, la DGII rechazará el comprobante (Error 302).",
      recommendation: "Usa 31 para transacciones B2B (Manejo de ITBIS) y 32 para Consumidores Finales."
    },
    "comprador-rnc": {
      fieldId: "comprador-rnc",
      label: "RNC o Cédula del Comprador",
      description: "Identificación tributaria del receptor del servicio o producto adquirido.",
      expectedFormat: "9 dígitos (RNC) u 11 dígitos (Cédula). Sin guiones.",
      exampleValue: "131103982",
      isRequired: false,
      validationRules: "Módulo DGII M11 (Checksum).",
      businessImpact: "En comprobantes tipo '32' (Consumo), este campo solo es obligatorio si la venta supera los RD$250,000.",
      recommendation: "Valida siempre el RNC contra el padrón antes de facturar."
    },
    "total-monto": {
      fieldId: "total-monto",
      label: "Cobro Total (RD$)",
      description: "Facturación bruta total expresada en pesos dominicanos.",
      expectedFormat: "Numérico decimal (0.00)",
      exampleValue: "15500.50",
      isRequired: true,
      businessImpact: "Define el ingreso oficial reportado en tu declaración del IT-1."
    },
    "transmision-agil": {
      fieldId: "transmision-agil",
      label: "Transmisión Ágil a DGII",
      description: "Habilita la sincronización en tiempo real del documento con el ambiente de Recepción de DGII.",
      isRequired: true,
      recommendation: "Mantén este checkbox activo a menos que estés emitiendo volúmenes masivos nocturnos (>10,000 facturas)."
    }
  }
};
