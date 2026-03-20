import asyncio
from playwright.async_api import async_playwright
import time
import os

# Settings
PROFILE_DIR = r"C:\selenium\perfil_dns_playwright"
BINARY_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ZONE_URL = "https://dash.cloudflare.com/efce4179a7ee96c19b43c42bced58587/getupsoft.com.do/dns/records"

if not os.path.exists(PROFILE_DIR):
    os.makedirs(PROFILE_DIR)

async def add_record(page, r_type, name, content, priority=None):
    print(f"[*] Intentando agregar {r_type} ({name})...")
    try:
        # Click Add Record - More robust selector
        await page.get_by_role("button", name="Add record").click()
        
        # Type Select
        await page.get_by_label("Type").click()
        # Find the specific type in the list
        await page.get_by_text(r_type, exact=True).first.click()
        
        # Name field
        await page.get_by_placeholder("example.com").fill(name)
        
        # Content / Server
        if r_type == "MX":
            await page.get_by_placeholder("mailserver.example.com").fill(content)
            if priority:
                await page.get_by_placeholder("10").fill(str(priority))
        else:
            await page.get_by_placeholder("v=spf1 ...").fill(content)
            
        # Save
        await page.get_by_role("button", name="Save").click()
        print(f"[✓] Registro {r_type} guardado.")
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[!] Error o ya existe: {e}")
        try:
            await page.get_by_role("button", name="Cancel").click()
        except: pass

async def main():
    print("="*60)
    print("  CLOUDFLARE DNS PLAYWRIGHT AUTOMATION")
    print("="*60)
    
    async with async_playwright() as p:
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            executable_path=BINARY_PATH,
            headless=False,
            viewport={'width': 1280, 'height': 800}
        )
        
        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
        
        print(f"[*] Navegando a {ZONE_URL}")
        await page.goto(ZONE_URL)
        
        print("[!] Esperando 60 segundos para LOGIN o BYPASS de Turnstile...")
        # Playwright usually handles wait_for_load_state, but we need time for manual user action
        await asyncio.sleep(60)
        
        records = [
            ("MX", "@", "mail.getupsoft.com.do", 10),
            ("TXT", "@", "v=spf1 include:_spf.google.com ~all", None),
            ("TXT", "_dmarc", "v=DMARC1; p=none; rua=mailto:admin@getupsoft.com.do", None)
        ]
        
        for r_type, name, content, prio in records:
            await add_record(page, r_type, name, content, prio)
            
        print("="*60)
        print("[*] Proceso terminado. Browser abierto por 2 minutos para revisión.")
        await asyncio.sleep(120)
        await browser_context.close()

if __name__ == "__main__":
    asyncio.run(main())
