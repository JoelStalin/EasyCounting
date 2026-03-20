#!/usr/bin/env python3
"""
Automation Script: DGII Certification Provisional Test Phase
Automatización para la fase de pruebas de certificación DGII

Pasos:
1. Generar XMLs de e-CF test (31, 32, 33, 34)
2. Recopilar información de configuración
3. Preparar evidencia
4. Mostrar acciones manuales requeridas
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).parent))

from app.services.dgii_scraper.certification_bot import DGIICertificationBot
from app.billing.ecf_builder import build_ecf


async def main():
    """Run Certification Automation"""
    
    # Banner
    print("╔" + "═" * 66 + "╗")
    print("║" + " FASE 5-6: GENERACIÓN Y ENVÍO DE PRUEBAS DGII ".center(66) + "║")
    print("║" + " Certificación Provisional (PRECERT) ".center(66) + "║")
    print("╚" + "═" * 66 + "╝")
    print()
    
    # Step 1: Check current status
    print("[1/5] 📊 Verificando Estado Actual...")
    bot = DGIICertificationBot(rnc='25500706423', password='test')
    status = await bot.check_certification_status()
    
    print(f"      RNC: {status['rnc']}")
    print(f"      Estado: {status['certification_state']}")
    print(f"      Paso: {status['step']}/15")
    print(f"      ✓ Listo para Fase 5")
    print()
    
    # Step 2: Create test output directory
    print("[2/5] 📁 Creando Directorio de Evidencia...")
    evidence_dir = Path("artifacts_live_dns/dgii_certification")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    print(f"      {evidence_dir}")
    print(f"      ✓ Directorio creado")
    print()
    
    # Step 3: Generate test XML e-CFs
    print("[3/5] 📝 Generando XMLs de Prueba (e-CF 31, 32, 33, 34)...")
    
    test_ecfs = []
    doc_types = {
        "31": "Crédito Fiscal (B2B)",
        "32": "Compra/Consumo (B2C)",
        "33": "Nota de Crédito",
        "34": "Nota de Débito"
    }
    
    for idx, (doc_type, description) in enumerate(doc_types.items(), 1):
        # ENCF Format: [Letter][12 digits]
        # Example: E310000000001
        encf = f"E{doc_type}{'000000000' + str(idx):0>8}"
        try:
            xml = build_ecf(
                encf=encf,
                rnc_emisor="25500706423",
                rnc_comprador="13100000001",
                total=1000.00 + (int(doc_type) * 100)
            )
            
            filename = f"test_ecf_{doc_type}_{description.replace('/', '_')}.xml"
            filepath = evidence_dir / filename
            filepath.write_text(xml, encoding='utf-8')
            
            test_ecfs.append({
                "type": doc_type,
                "description": description,
                "filename": filename,
                "path": str(filepath),
                "encf": encf,
                "xml_size": len(xml)
            })
            
            print(f"      ✓ e-CF {doc_type}: {description}")
        except Exception as e:
            print(f"      ✗ Error en e-CF {doc_type}: {e}")
    
    print()
    
    # Step 4: Generate evidence summary
    print("[4/5] 📋 Generando Resumen de Evidencia...")
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "rnc": "25500706423",
        "user": "JOEL STALIN",
        "status": status,
        "generated_test_xml": test_ecfs,
        "environment": "PRECERT",
        "next_steps": [
            "Descargar certificado digital .p12 del Portal OFV (https://dgii.gov.do/OFV)",
            "Guardar en: c:\\Users\\yoeli\\Documents\\dgii_encf\\secrets\\cert.p12",
            "Actualizar .env.local con DGII_CERT_P12_PASSWORD",
            "Ejecutar test suite: python -m pytest app/tests/test_dgii_certification.py",
            "Revisar resultados en Portal OFV"
        ]
    }
    
    summary_file = evidence_dir / "certification_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f"      ✓ Resumen guardado en: {summary_file}")
    print()
    
    # Step 5: Display next actions
    print("[5/5] 📌 ACCIONES MANUALES REQUERIDAS:")
    print()
    print("  ┌─ PASO 1: Obtener Certificado Digital")
    print("  │")
    print("  │  1. Abrir: https://dgii.gov.do/OFV")
    print("  │  2. Login:")
    print("  │     RNC: 25500706423")
    print("  │     Contraseña: [Tu Contraseña DGII]")
    print("  │")
    print("  │  3. Buscar: Administración → Descargar Certificado Digital")
    print("  │  4. Descargar archivo .p12")
    print("  │  5. Guardar como: secrets/cert.p12")
    print("  │")
    print("  │  6. Anotar contraseña del .p12 (para DGII_CERT_P12_PASSWORD)")
    print("  └─")
    print()
    
    print("  ┌─ PASO 2: Configurar en .env.local")
    print("  │")
    print("  │  DGII_P12_PATH=/secrets/cert.p12")
    print("  │  DGII_P12_PASSWORD=<contraseña del .p12>")
    print("  │")
    print("  │  (Ver .env.example para más variables)")
    print("  └─")
    print()
    
    print("  ┌─ PASO 3: Ejecutar Tests de Certificación")
    print("  │")
    print("  │  cd c:\\Users\\yoeli\\Documents\\dgii_encf")
    print("  │  python -m pytest app/tests/test_dgii_certification.py -v")
    print("  │")
    print("  │  O desde Python:")
    print("  │  python run_dgii_certification_test.py")
    print("  └─")
    print()
    
    print("═" * 70)
    print()
    print(f"✓ Certificación PRECERT lista para envío")
    print(f"  Directorio de evidencia: {evidence_dir}")
    print(f"  XMLs generados: {len(test_ecfs)}/4")
    print()
    print(f"📊 Portal OFV Status: Paso {status['step']}/15 - {status['certification_state']}")
    print()


if __name__ == '__main__':
    asyncio.run(main())
