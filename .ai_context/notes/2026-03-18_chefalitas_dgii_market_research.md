# Chefalitas DGII And Market Research - 2026-03-18

## Research scope

This note consolidates two lines of research relevant to the Chefalitas/Odoo request:

1. DGII reporting and filing mechanics
2. Current market positioning and pricing references in the Dominican Republic

## 1. DGII reporting mechanics

### 1.1 Official filing path for 606/607/608/609

Current official DGII material shows that 606/607/608/609 are handled as TXT-based "Formatos de Envio de Datos" submitted through Oficina Virtual DGII.

Relevant current official points:

- DGII provides a pre-validation tool for 606, 607 and 608.
- 606 should be sent before the ITBIS filing deadline when related credits need to be accepted.
- Informative/in-zero submission exists through the `Declaraciones en Cero` path in OFV.
- The generic remittance path is still:
  - generate TXT
  - access OFV
  - choose `Enviar Archivos`
  - pick the format
  - attach the TXT
  - send the data

### 1.2 What this means for Chefalitas

The existing Odoo report module already covers the TXT generation side. What is missing is the submission side, but that submission side appears to remain an OFV workflow rather than a public documented DGII API for these formats.

Practical implication:

- the immediate product gap is not "generate 606/607/608/609"
- the immediate gap is "traceable OFV submission support and compliance workflow"

### 1.3 Important e-CF nuance

Official DGII guidance and help content indicate that when a taxpayer operates with 100% electronic invoicing:

- 607 and 608 may no longer be required in the same way
- in mixed periods, only the non-electronic `serie B` documents may still need to be reported
- purchases and other obligations such as 606 can still remain relevant

Therefore, before changing Chefalitas reporting logic, the actual fiscal operating mode of the company must be confirmed.

## 2. Video/tutorial research

I did not use Gemini through Selenium as an intermediary because it would add an unnecessary third-party layer and would not improve source quality. I used direct source research instead.

Useful current official/public discovery points:

- DGII pages for 606 and `Formatos de Envio de Datos` explicitly reference `Videos Instructivos`
- DGII news pages reference the institutional program `DGII 360` and state that previous editions are available on DGII's YouTube channel
- DGII 360 episodes are being used to explain:
  - facturacion electronica
  - implementation deadlines
  - platform behavior and process updates

This is the right source family for process-understanding videos, not unofficial tutorials.

## 3. Dominican market references

### 3.1 Zero-price floor

DGII continues to promote `Facturador Gratuito` as a no-cost option for eligible taxpayers. That means the market floor is effectively `RD$0` for contributors who qualify and accept the limits of the government tool.

### 3.2 SaaS market samples found

These were visible from current public pricing pages on 2026-03-18:

- DigitalHorizon RD:
  - `RD$990/mes` for 100 e-CF
  - `RD$1,590/mes` for 300 e-CF
  - `RD$2,300/mes` for 500 e-CF
  - `RD$3,850/mes` for 1,000 e-CF
  - modular ERP upsells from `RD$900` to `RD$2,500` monthly
- Digimart:
  - `$24.99/mes` entry
  - `$49.99/mes` business
  - `$79.99/mes` pro
  - all with 100 e-CF included and incremental pricing beyond that
- Dealers Admin:
  - starts from `US$49.99/mes` billed annually
  - broader vertical ERP/dealer positioning with DGII reports included

### 3.3 Market interpretation

The Dominican market currently appears segmented into at least four pricing bands:

1. `RD$0`
   - DGII Facturador Gratuito
   - target: micro/eligible low-complexity users
2. `RD$990` to `RD$2,500` monthly
   - entry e-CF SaaS with basic portal/API capabilities
   - target: micro and small businesses
3. `RD$3,500` to `RD$7,000` monthly
   - stronger operational packages, multi-user, multi-branch, accounting extras
4. `US$49.99+` monthly
   - verticalized or broader ERP systems

### 3.4 Pricing implication for a Chefalitas/GetUpSoft-style product

If the offer includes:

- DGII e-CF
- Odoo ERP
- POS
- customer portal
- partner/supplier portal
- 606/607/608/609 generation
- local support and implementation

then the product is **not** competing with the free government tool. It is competing with the lower-mid to mid-tier SaaS/ERP band.

A reasonable market framing would likely need:

- a low entry plan close to the `RD$990-RD$1,500` range only if the feature set is intentionally narrow
- a restaurant/POS operational plan above the bare e-CF tools
- implementation/setup priced separately from monthly SaaS
- optional compliance/support bundles for report handling and certification assistance

## 4. Current recommendation

Before setting final prices:

1. confirm Chefalitas target segment:
   - micro business
   - restaurant SME
   - multi-branch chain
2. separate recurring SaaS from one-time implementation
3. separate compliance help from core software price
4. do not price below DGII-free alternatives unless the strategy is purely penetration-based

## Official/public sources reviewed on 2026-03-18

- DGII Formato 606:
  - `https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscales/Paginas/Formato-606.aspx`
- DGII Formatos de Envio de Datos:
  - `https://dgii.gov.do/cicloContribuyente/obligacionesTributarias/remisionInformacion/Paginas/formatoEnvioDatos.aspx`
- DGII Biblioteca de formatos:
  - `https://dgii.gov.do/publicacionesOficiales/bibliotecaVirtual/contribuyentes/formatoEnvioDatos/Paginas/default.aspx`
- DGII infographic for sending data formats:
  - `https://dgii.gov.do/publicacionesOficiales/bibliotecaVirtual/Infografias/Infografia%20C%C3%B3mo%20Remitir%20los%20Formatos%20de%20Env%C3%ADo%20de%20Datos%20a%20la%20DGII.pdf`
- DGII Facturador Gratuito:
  - `https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/facturador-gratuito.aspx`
- DGII benefits of e-invoicing:
  - `https://dgii.gov.do/publicacionesOficiales/bibliotecaVirtual/Infografias/Beneficios%20de%20la%20Facturacion%20Electronica.pdf`
- DGII 360 facturacion electronica note:
  - `https://dgii.gov.do/noticias/Paginas/Ya-te-sumaste-a-la-Facturacion-Electronica.aspx`
- DigitalHorizon pricing:
  - `https://digitalhorizonrd.com/`
- Digimart pricing:
  - `https://www.digimart.cloud/`
- Dealers Admin pricing:
  - `https://www.dealersadmin.com/`
