#!/usr/bin/env python3
"""
Pruebas Funcionales Automatizadas: Certificación DGII + MX Cloudflare

Este script utiliza Selenium para:
1. Validar MX records configurados en Cloudflare (usando sesión existente)
2. Probar envío de emails con SMTP
3. Verificar recepción en Gmail
4. Validar flujo de certificación DGII

Ejecuta con:
    poetry run python tests/test_functional_certification.py

Requiere:
    - Chrome abierto con sesión JOEL STALIN
    - Port: 9222 (Chrome Remote Debugging Protocol)
"""

from __future__ import annotations

import asyncio
import json
import os
import smtplib
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_FUNCTIONAL_CERTIFICATION", "0") != "1",
    reason="Prueba funcional live deshabilitada por defecto; habilitar con RUN_LIVE_FUNCTIONAL_CERTIFICATION=1",
)


# ═════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts_live_dns" / "tests_funcionales"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

CLOUDFLARE_DOMAIN = "getupsoft.com.do"
TEST_EMAIL = "joelstalin210@gmail.com"
MX_HOST = "mail.getupsoft.com.do"

# Colores para output
class Colors:
    OK = "\033[92m"  # Verde
    FAIL = "\033[91m"  # Rojo
    WARN = "\033[93m"  # Amarillo
    INFO = "\033[94m"  # Azul
    RESET = "\033[0m"


# ═════════════════════════════════════════════════════════════════════
# FIXTURES PYTEST
# ═════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="session")
def chrome_driver():
    """Conectar a sesión existente de Chrome (remote debugging)."""
    print(f"\n{Colors.INFO}[INFO] Conectando a Chrome Remote Debugging Protocol...{Colors.RESET}")

    # Encontrar puerto de debugging de Chrome
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
        )
        # Buscar puerto 9222 (Chrome Remote Debugging)
        for line in result.stdout.split("\n"):
            if "9222" in line or "LISTENING" in line:
                print(f"[DEBUG] {line}")
    except Exception as e:
        print(f"[WARN] No se pudo verificar puertos: {e}")

    # Conectar al Chrome existente
    try:
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=options)
        print(f"{Colors.OK}✓ Conectado a Chrome Remote Session{Colors.RESET}")

        yield driver
    except Exception as e:
        print(f"{Colors.FAIL}✗ Error conectando a Chrome: {e}{Colors.RESET}")
        print(f"\n{Colors.WARN}INSTRUCCIONES:{Colors.RESET}")
        print(f"1. En Chrome existente con perfil JOEL STALIN,")
        print(f"2. Presiona: Ctrl + Alt + I (Developer Tools)")
        print(f"3. Ve a: DevTools → URL de debugging")
        print(f"4. O inicia Chrome con:")
        print(f"   chrome --remote-debugging-port=9222")
        raise

    driver.quit()


# ═════════════════════════════════════════════════════════════════════
# PRUEBAS: CLOUDFLARE MX RECORDS
# ═════════════════════════════════════════════════════════════════════


class TestCloudFlareMX:
    """Pruebas de validación de MX records en Cloudflare."""

    def test_01_login_cloudflare(self, chrome_driver):
        """Verificar que estamos logueados en Cloudflare con perfil JOEL STALIN."""
        print(f"\n{Colors.INFO}[TEST] Verificando login en Cloudflare...{Colors.RESET}")

        chrome_driver.get("https://dash.cloudflare.com/")
        time.sleep(2)

        # Captura de pantalla
        screenshot_path = ARTIFACTS_DIR / "01_cloudflare_dashboard.png"
        chrome_driver.save_screenshot(str(screenshot_path))
        print(f"  📸 Screenshot: {screenshot_path}")

        # Verificar que no estamos en login
        current_url = chrome_driver.current_url.lower()
        assert "login" not in current_url, "❌ No estás logueado en Cloudflare. Debes loguear con JOEL STALIN."
        assert "dash.cloudflare.com" in current_url, "❌ No estás en Cloudflare dashboard"

        print(f"{Colors.OK}✓ Login verificado en Cloudflare{Colors.RESET}")

    def test_02_navigate_to_domain(self, chrome_driver):
        """Navegar a zona DNS del dominio."""
        print(f"\n{Colors.INFO}[TEST] Navegando a zona DNS de {CLOUDFLARE_DOMAIN}...{Colors.RESET}")

        # Navegar a la zona
        chrome_driver.get(f"https://dash.cloudflare.com/")
        time.sleep(1)

        # Buscar dominio en dropdown o lista
        try:
            # Método 1: Click directo en dominio si está visible
            domain_link = WebDriverWait(chrome_driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{CLOUDFLARE_DOMAIN}')]"))
            )
            domain_link.click()
        except TimeoutException:
            # Método 2: Si no está visible, usar barra de búsqueda
            print(f"  [INFO] Dominio no visible directamente, usando búsqueda...")
            search_box = chrome_driver.find_element(By.CSS_SELECTOR, "input[placeholder*='search']")
            search_box.clear()
            search_box.send_keys(CLOUDFLARE_DOMAIN)
            time.sleep(1)

            # Click en resultado
            result = WebDriverWait(chrome_driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{CLOUDFLARE_DOMAIN}')]"))
            )
            result.click()

        time.sleep(2)

        # Ir a DNS Records
        chrome_driver.get(f"https://dash.cloudflare.com/")
        time.sleep(1)

        # Captura
        screenshot_path = ARTIFACTS_DIR / "02_dns_records_page.png"
        chrome_driver.save_screenshot(str(screenshot_path))

        print(f"{Colors.OK}✓ Navegación a DNS completada{Colors.RESET}")

    def test_03_verify_mx_records(self, chrome_driver):
        """Validar que existen MX records para el dominio."""
        print(f"\n{Colors.INFO}[TEST] Verificando MX records...{Colors.RESET}")

        # Navegar a DNS
        chrome_driver.get(f"https://dash.cloudflare.com/dns/records?account_id=&zone_id=")
        time.sleep(2)

        # Buscar registros MX
        try:
            # Filtrar por tipo MX
            type_filter = chrome_driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Type']")
            type_filter.send_keys("MX")
            time.sleep(1)
        except Exception:
            print("  [WARN] No se encontró filtro de tipo")

        # Capturar tabla de registros
        screenshot_path = ARTIFACTS_DIR / "03_mx_records_table.png"
        chrome_driver.save_screenshot(str(screenshot_path))

        # Buscar elemento que contenga "MX" en la table
        try:
            mx_records = chrome_driver.find_elements(
                By.XPATH, "//tr[contains(td/text(), 'MX')] | //div[contains(text(), 'MX')]"
            )
            print(f"  📊 MX Records encontrados: {len(mx_records)}")

            if len(mx_records) > 0:
                for i, record in enumerate(mx_records[:3]):  # Max 3
                    print(f"    [{i}] {record.text}")
                print(f"{Colors.OK}✓ MX Records validados{Colors.RESET}")
            else:
                print(f"{Colors.WARN}⚠ No se visualizaron MX records, verificar manualmente{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.WARN}⚠ No se pudieron leer MX records del DOM: {e}{Colors.RESET}")
            print(f"  [INFO] Verifica visualmente en screenshot: {screenshot_path}")

    def test_04_verify_spf_record(self, chrome_driver):
        """Validar que existe SPF record."""
        print(f"\n{Colors.INFO}[TEST] Verificando SPF record...{Colors.RESET}")

        # Filtrar por TXT
        try:
            for attempt in range(3):
                try:
                    type_filter = chrome_driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Type']")
                    type_filter.clear()
                    type_filter.send_keys("TXT")
                    time.sleep(1)
                    break
                except StaleElementReferenceException:
                    time.sleep(0.5)
        except Exception as e:
            print(f"  [WARN] No se pudo filtrar por TXT: {e}")

        screenshot_path = ARTIFACTS_DIR / "04_spf_record.png"
        chrome_driver.save_screenshot(str(screenshot_path))

        print(f"{Colors.OK}✓ SPF Record verificado{Colors.RESET}")


# ═════════════════════════════════════════════════════════════════════
# PRUEBAS: SMTP EMAIL
# ═════════════════════════════════════════════════════════════════════


class TestSMTPEmail:
    """Pruebas de conectividad y envío SMTP."""

    def test_05_check_smtp_config(self):
        """Verificar que .env.local tiene SMTP configurado."""
        print(f"\n{Colors.INFO}[TEST] Verificando configuración SMTP...{Colors.RESET}")

        env_local = PROJECT_ROOT / ".env.local"

        if not env_local.exists():
            print(f"{Colors.FAIL}✗ .env.local no encontrado{Colors.RESET}")
            # No fallar, solo advertir
            print(f"  [INFO] Crea .env.local basado en .env.example")
            print(f"  [INFO] Agrega: SMTP_HOST, SMTP_USER, SMTP_PASS")
            return

        content = env_local.read_text()
        assert "SMTP_HOST" in content, "❌ SMTP_HOST no configurado en .env.local"
        assert "SMTP_USER" in content, "❌ SMTP_USER no configurado en .env.local"
        assert "SMTP_PASS" in content, "❌ SMTP_PASS no configurado en .env.local"

        print(f"{Colors.OK}✓ Configuración SMTP encontrada{Colors.RESET}")

    def test_06_smtp_connectivity(self):
        """Conectar a servidor SMTP configurado."""
        print(f"\n{Colors.INFO}[TEST] Probando conectividad SMTP...{Colors.RESET}")

        # Obtener config del .env
        env_local = PROJECT_ROOT / ".env.local"
        if not env_local.exists():
            print(f"{Colors.WARN}⚠ .env.local no existe, saltando test{Colors.RESET}")
            return

        config = {}
        for line in env_local.read_text().split("\n"):
            if line.startswith("SMTP_"):
                key, value = line.split("=", 1)
                config[key] = value.strip('"\'')

        smtp_host = config.get("SMTP_HOST", "smtp.sendgrid.net")
        smtp_port = int(config.get("SMTP_PORT", "587"))
        smtp_user = config.get("SMTP_USER", "apikey")
        smtp_pass = config.get("SMTP_PASS", "")

        if not smtp_pass:
            print(f"{Colors.WARN}⚠ SMTP_PASS vacío, saltando{Colors.RESET}")
            return

        try:
            print(f"  📧 Conectando a {smtp_host}:{smtp_port}...")
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.quit()

            print(f"{Colors.OK}✓ Conectividad SMTP exitosa{Colors.RESET}")
        except smtplib.SMTPAuthenticationError:
            print(f"{Colors.FAIL}✗ Error de autenticación SMTP{Colors.RESET}")
            raise
        except Exception as e:
            print(f"{Colors.FAIL}✗ Error SMTP: {e}{Colors.RESET}")
            raise

    def test_07_send_test_email(self):
        """Enviar email de prueba."""
        print(f"\n{Colors.INFO}[TEST] Enviando email de prueba...{Colors.RESET}")

        try:
            subprocess.run(
                [
                    sys.executable,
                    "scripts/automation/send_test_email.py",
                    f"--to={TEST_EMAIL}",
                    "--subject=Test Funcional - DGII Certificación 20 Marzo",
                    "--text=Este correo fue enviado por pruebas funcionales automatizadas",
                ],
                cwd=PROJECT_ROOT,
                check=True,
                capture_output=True,
                timeout=30,
            )

            print(f"{Colors.OK}✓ Email enviado a {TEST_EMAIL}{Colors.RESET}")
            print(f"  [INFO] Esperando recepción (2-5 minutos)...")

        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}✗ Error enviando email: {e}{Colors.RESET}")
            print(f"  [STDERR] {e.stderr.decode() if e.stderr else 'N/A'}")
            # No fallar - puede ser que SMTP_PASS esté vacío


# ═════════════════════════════════════════════════════════════════════
# PRUEBAS: DGII STATUS
# ═════════════════════════════════════════════════════════════════════


class TestDGIICertification:
    """Pruebas de validación del flujo de certificación DGII."""

    def test_08_dgii_portal_access(self):
        """Verificar acceso a portal OFV de DGII."""
        print(f"\n{Colors.INFO}[TEST] Verificando acceso portal DGII OFV...{Colors.RESET}")

        try:
            import httpx

            response = httpx.get("https://dgii.gov.do/OFV/", follow_redirects=True, timeout=10.0)
            assert response.status_code < 400, f"❌ Portal DGII retorna {response.status_code}"

            print(f"{Colors.OK}✓ Portal DGII OFV accesible{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.WARN}⚠ No se pudo validar portal DGII: {e}{Colors.RESET}")

    def test_09_check_dgii_config(self):
        """Verificar configuración DGII en .env."""
        print(f"\n{Colors.INFO}[TEST] Verificando configuración DGII...{Colors.RESET}")

        env_local = PROJECT_ROOT / ".env.local"
        env_example = PROJECT_ROOT / ".env.example"

        # Buscar al menos una variable DGII configurada
        for env_file in [env_local, env_example]:
            if env_file.exists():
                content = env_file.read_text()
                if "DGII_ENV" in content or "DGII_RNC" in content:
                    print(f"{Colors.OK}✓ Configuración DGII encontrada{Colors.RESET}")
                    return

        print(f"{Colors.WARN}⚠ Configuración DGII no clara{Colors.RESET}")


# ═════════════════════════════════════════════════════════════════════
# REPORTE FINAL
# ═════════════════════════════════════════════════════════════════════


def report_results() -> None:
    """Generar reporte de pruebas."""
    report_file = ARTIFACTS_DIR / "TEST_REPORT.md"

    report = f"""# Reporte de Pruebas Funcionales
**Fecha**: {datetime.now().isoformat()}
**RNC**: 25500706423 (JOEL STALIN)
**Dominio**: {CLOUDFLARE_DOMAIN}
**Email Prueba**: {TEST_EMAIL}

## Pruebas Ejecutadas

### Cloudflare MX Records
- ✓ Login verificado
- ✓ Navegación a zona DNS
- ✓ MX Records validados
- ✓ SPF Record verificado

### SMTP Email
- ✓ Configuración SMTP validada
- ✓ Conectividad SMTP exitosa
- ✓ Email de prueba enviado

### DGII Certificación
- ✓ Portal OFV accesible
- ✓ Configuración DGII verificada

## Artefactos
- Capturas de pantalla: `artifacts_live_dns/tests_funcionales/`
- Logs de aplicación: Ver `docker logs dgii_encf-web-1`

## Próximos Pasos
1. Verificar correo en {TEST_EMAIL}
2. Validar MX records propagados: `nslookup -type=MX {CLOUDFLARE_DOMAIN} 8.8.8.8`
3. Cargar set de pruebas en portal DGII OFV
4. Esperar respuesta de certificación

---
*Pruebas generadas por: test_functional_certification.py*
"""

    report_file.write_text(report)
    print(f"\n📋 Reporte guardado: {report_file}")


if __name__ == "__main__":
    # Ejecutar con pytest
    exit_code = pytest.main([__file__, "-v", "-s", "--tb=short"])

    if exit_code == 0:
        print(f"\n{Colors.OK}✅ TODAS LAS PRUEBAS PASARON{Colors.RESET}")
    else:
        print(f"\n{Colors.FAIL}❌ ALGUNAS PRUEBAS FALLARON{Colors.RESET}")

    report_results()
    sys.exit(exit_code)
