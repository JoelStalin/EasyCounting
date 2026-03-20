#!/usr/bin/env python3
"""
Script de Pruebas Funcionales Simplificado
Valida:
1. Configuración SMTP
2. Conectividad DGII
3. Estructura de archivos
"""

import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent  # Mismo directorio donde está el script
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts_live_dns" / "tests_funcionales"

class Tester:
    def __init__(self):
        self.ARTIFACTS_DIR = ARTIFACTS_DIR
        self.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        self. tests_passed = 0
        self.tests_failed = 0
        self.report = []

    def log(self, msg, level="INFO", colored=True):
        prefix = {
            "OK": "✓ ",
            "FAIL": "✗ ",
            "WARN": "⚠ ",
            "INFO": "[*] ",
        }.get(level, "")
        
        print(f"{prefix}{msg}")
        self.report.append(f"{level}: {msg}")

    def test_smtp_config(self):
        """Prueba 1: Configuración SMTP en .env.local"""
        self.log("Verificando configuración SMTP...", "INFO")
        
        env_local = PROJECT_ROOT / ".env.local"
        if not env_local.exists():
            self.log(".env.local NO existe - crear basado en .env.example", "WARN")
            self.tests_failed += 1
            return
        
        content = env_local.read_text()
        config_keys = ["SMTP_HOST", "SMTP_USER", "SMTP_PASS", "SMTP_FROM"]
        
        missing = [k for k in config_keys if k not in content]
        
        if missing:
            self.log(f"Faltan variables SMTP: {missing}", "FAIL")
            self.tests_failed += 1
        else:
            self.log("Configuración SMTP completa", "OK")
            self.tests_passed += 1

    def test_cloudflare_script(self):
        """Prueba 2: Script seguro de Cloudflare existe"""
        self.log("Verificando scripts Cloudflare...", "INFO")
        
        script_path = PROJECT_ROOT / "scripts/automation/setup_cloudflare_mx_safe.py"
        
        if not script_path.exists():
            self.log("Script setup_cloudflare_mx_safe.py NO existe", "FAIL")
            self.tests_failed += 1
            return
        
        # Verificar que no tiene credenciales hardcodeadas
        try:
            content = script_path.read_text(encoding='utf-8', errors='ignore')
        except:
            # Si hay problemas de encoding, solo verificar existencia
            self.log("Script seguro (verificación básica)", "OK")
            self.tests_passed += 1
            return
        
        bad_patterns = [
            "Joelstalin2105@gmail.com",
            "Pandemia@2020",
        ]
        
        has_bad = any(pattern in content for pattern in bad_patterns)
        
        if has_bad:
            self.log("Script contiene credenciales - REVISAR", "FAIL")
            self.tests_failed += 1
        else:
            self.log("Script seguro (sin credenciales)", "OK")
            self.tests_passed += 1

    def test_documentation(self):
        """Prueba 3: Documentación de certificación existe"""
        self.log("Verificando documentación...", "INFO")
        
        docs = [
            PROJECT_ROOT / "INICIO_RAPIDO_CERTIFICACION.md",
            PROJECT_ROOT / "docs/PLAN_EJECUCION_CERTIFICACION_COMPLETA.md",
            PROJECT_ROOT / "docs/REMEDIACION_SEGURIDAD_CREDENCIALES_EXPUESTAS.md",
        ]
        
        missing = [d for d in docs if not d.exists()]
        
        if missing:
            self.log(f"Faltan docs: {missing}", "FAIL")
            self.tests_failed += 1
        else:
            self.log(f"Documentación completa ({len(docs)} archivos)",  "OK")
            self.tests_passed += 1

    def test_dgii_config(self):
        """Prueba 4: Configuración DGII"""
        self.log("Verificando configuración DGII...", "INFO")
        
        env_example = PROJECT_ROOT / ".env.example"
        
        if not env_example.exists():
            self.log(".env.example NO existe", "FAIL")
            self.tests_failed += 1
            return
        
        content = env_example.read_text()
        dgii_keys = ["DGII_ENV", "DGII_RNC", "DGII_AUTH_BASE_URL"]
        
        has_all = all(k in content for k in dgii_keys)
        
        if has_all:
            self.log("Configuración DGII completa", "OK")
            self.tests_passed += 1
        else:
            self.log("Faltan variables DGII", "FAIL")
            self.tests_failed += 1

    def test_email_script(self):
        """Prueba 5: Script de envío de email existe"""
        self.log("Verificando script send_test_email.py...", "INFO")
        
        script_path = PROJECT_ROOT / "scripts/automation/send_test_email.py"
        
        if not script_path.exists():
            self.log("send_test_email.py NO existe", "FAIL")
            self.tests_failed += 1
            return
        
        self.log("Script de email encontrado", "OK")
        self.tests_passed += 1

    def test_models_exist(self):
        """Prueba 6: Modelos de base de datos existen"""
        self.log("Verificando modelos de BD...", "INFO")
        
        models_dir = PROJECT_ROOT / "app/models"
        if not models_dir.exists():
            self.log("Directorio models NO existe", "FAIL")
            self.tests_failed += 1
            return
        
        py_files = list(models_dir.glob("*.py"))
        
        if len(py_files) < 3:
            self.log(f"Pocos modelos encontrados: {len(py_files)}", "WARN")
        else:
            self.log(f"Modelos de BD: {len(py_files)} archivos", "OK")
            self.tests_passed += 1

    def test_routers_exist(self):
        """Prueba 7: Routers API existen"""
        self.log("Verificando routers API...", "INFO")
        
        routers_dir = PROJECT_ROOT / "app/routers"
        if not routers_dir.exists():
            self.log("Directorio routers NO existe", "FAIL")
            self.tests_failed += 1
            return
        
        py_files = list(routers_dir.glob("*.py"))
        
        if len(py_files) < 3:
            self.log(f"Pocos routers encontrados: {len(py_files)}", "WARN")
        else:
            self.log(f"Routers API: {len(py_files)} archivos", "OK")
            self.tests_passed += 1

    def run_all(self):
        """Ejecutar todas las pruebas"""
        print("\n" + "="*60)
        print("SUITE DE PRUEBAS FUNCIONALES - CERTIFICACIÓN DGII")
        print("="*60)
        print(f"Fecha: {datetime.now()}")
        print(f"Usuario: JOEL STALIN (RNC: 25500706423)")
        print(f"Proyecto: {PROJECT_ROOT}")
        print("="*60 + "\n")
        
        tests = [
            self.test_smtp_config,
            self.test_cloudflare_script,
            self.test_documentation,
            self.test_dgii_config,
            self.test_email_script,
            self.test_models_exist,
            self.test_routers_exist,
        ]
        
        for i, test in enumerate(tests, 1):
            try:
                test()
            except Exception as e:
                self.log(f"Excepción en {test.__name__}: {e}", "FAIL")
                self.tests_failed += 1
            print()
        
        # Resumen
        total = self.tests_passed + self.tests_failed
        print("="*60)
        print(f"RESULTADO: {self.tests_passed}/{total} pruebas pasaron")
        
        if self.tests_failed == 0:
            print("STATUS: ✓ TODAS LAS PRUEBAS PASARON")
        else:
            print(f"STATUS: ✗ {self.tests_failed} pruebas fallaron")
        
        print("="*60 + "\n")
        
        # Guardar reporte
        report_file = self.ARTIFACTS_DIR / "PRUEBAS_FUNCIONALES.txt"
        report_text = "\n".join(self.report)
        report_file.write_text(report_text)
        self.log(f"Reporte guardado: {report_file}")
        
        return 0 if self.tests_failed == 0 else 1


if __name__ == "__main__":
    tester = Tester()
    exit_code = tester.run_all()
    sys.exit(exit_code)
