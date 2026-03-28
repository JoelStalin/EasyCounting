from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from e2e.support import record_step, wait_for_ready


def test_client_odoo_integration_generates_token(driver, client_url):
    driver.get(f"{client_url}/integrations/odoo")
    wait_for_ready(driver)
    record_step(driver, "client_odoo_redirect_to_login")

    WebDriverWait(driver, 20).until(EC.url_contains("/login"))
    email = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "email")))
    password = driver.find_element(By.ID, "password")
    email.send_keys("cliente@getupsoft.com.do")
    password.send_keys("Tenant123!")
    record_step(driver, "client_odoo_login_form_filled")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 20).until(EC.url_contains("/integrations/odoo"))
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'API Odoo para clientes empresariales')]"))
    )
    record_step(driver, "client_odoo_page_open")

    integration_name = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//span[contains(., 'Nombre de la integracion')]/../input"))
    )
    integration_name.clear()
    integration_name.send_keys("Odoo QA Selenium")
    driver.find_element(By.XPATH, "//button[normalize-space()='Generar token']").click()

    token_title = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Token generado')]"))
    )
    token_textarea = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//section//*[contains(., 'Token generado')]/following::textarea[1]"))
    )
    record_step(driver, "client_odoo_token_generated")
    assert "Token generado" in token_title.text
    assert token_textarea.get_attribute("value")

    endpoint_hint = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(., '/api/v1/tenant-api/invoices')]"))
    )
    record_step(driver, "client_odoo_endpoints_visible")
    assert "/api/v1/tenant-api/invoices" in endpoint_hint.text
