"""
Automation: Cloudflare DNS Setup
Bypasses Turnstile by using a persistent profile and allowing manual intervention.
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Settings
PROFILE_DIR = r"C:\selenium\perfil_dns"
BINARY_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

if not os.path.exists(PROFILE_DIR):
    os.makedirs(PROFILE_DIR)

opts = Options()
opts.binary_location = BINARY_PATH
opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
opts.add_experimental_option("detach", True)

def main():
    print("="*60)
    print("  CLOUDFLARE DNS SELF-SERVICE AUTOMATION")
    print("="*60)
    print(f"[*] Usando perfil persistente: {PROFILE_DIR}")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        
        # Navigate to Zone
        target_url = "https://dash.cloudflare.com/efce4179a7ee96c19b43c42bced58587/getupsoft.com.do/dns/records"
        driver.get(target_url)
        
        print("[!] Por favor inicia sesión si es necesario y resuelve cualquier verificación.")
        print("[!] Tienes 60 segundos para que la tabla de DNS sea visible.")
        time.sleep(60)
        
        records = [
            ("MX", "@", "mail.getupsoft.com.do", 10),
            ("TXT", "@", "v=spf1 include:_spf.google.com ~all", None),
            ("TXT", "_dmarc", "v=DMARC1; p=none; rua=mailto:admin@getupsoft.com.do", None)
        ]
        
        added = 0
        for r_type, name, content, prio in records:
            print(f"[*] Intentando agregar {r_type} ({name})...")
            try:
                # Add Record Button
                add_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add record')]"))
                )
                add_btn.click()
                
                # Type Select
                type_box = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'dns-record-type-select')]"))
                )
                type_box.click()
                time.sleep(1)
                
                opt_xpath = f"//div[text()='{r_type}'] | //div[contains(@data-testid, 'dns-type-{r_type}')]"
                option = driver.find_element(By.XPATH, opt_xpath)
                option.click()
                
                # Field identification
                name_field = driver.find_element(By.NAME, "name")
                name_field.clear()
                name_field.send_keys(name)
                
                if r_type == "MX":
                    server_field = driver.find_element(By.NAME, "exchange")
                    server_field.clear()
                    server_field.send_keys(content)
                    if prio:
                        prio_field = driver.find_element(By.NAME, "priority")
                        prio_field.clear()
                        prio_field.send_keys(str(prio))
                else:
                    content_field = driver.find_element(By.NAME, "content")
                    content_field.clear()
                    content_field.send_keys(content)
                
                # Save
                save_btn = driver.find_element(By.XPATH, "//button[contains(., 'Save')]")
                save_btn.click()
                print(f"[✓] Registro {r_type} guardado con éxito.")
                added += 1
                time.sleep(5)
                
            except Exception as e:
                print(f"[!] No se pudo agregar {r_type} {name} (posiblemente ya existe).")
                try:
                    driver.find_element(By.XPATH, "//button[contains(., 'Cancel')]").click()
                except: pass
                time.sleep(2)
                
        print("="*60)
        print(f"[*] Proceso terminado. {added}/{len(records)} registros procesados.")
        print("[*] Cerramos el script pero dejamos el browser abierto.")

    except Exception as e:
        print(f"[X] FATAL: {e}")

if __name__ == "__main__":
    main()
