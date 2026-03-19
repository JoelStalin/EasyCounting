import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from e2e.support import record_step, wait_for_ready


def test_admin_login_create_company_and_open_detail(driver, admin_url):
    suffix = str(int(time.time() * 1000))[-8:]
    company_name = f"Empresa Selenium {suffix}"
    company_rnc = f"131{suffix}"

    driver.get(f"{admin_url}/companies")
    wait_for_ready(driver)
    record_step(driver, "admin_redirect_to_login")

    WebDriverWait(driver, 20).until(EC.url_contains("/login"))
    email = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "email")))
    password = driver.find_element(By.ID, "password")
    email.send_keys("admin@getupsoft.com.do")
    password.send_keys("ChangeMe123!")
    record_step(driver, "admin_login_form_filled")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 20).until(EC.url_contains("/companies"))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'Compa')]")))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.LINK_TEXT, "Empresa Demo")))
    record_step(driver, "admin_companies_loaded")

    driver.get(f"{admin_url}/ai-providers")
    WebDriverWait(driver, 20).until(EC.url_contains("/ai-providers"))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'Agentes IA')]")))
    record_step(driver, "admin_ai_providers_open")

    driver.get(f"{admin_url}/companies")
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'Compa')]")))

    driver.find_element(By.XPATH, "//button[contains(., 'Crear compa')]").click()
    name_input = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//label[contains(., 'Nombre')]//input"))
    )
    rnc_input = driver.find_element(By.XPATH, "//label[contains(., 'RNC')]//input")
    env_select = Select(driver.find_element(By.XPATH, "//label[contains(., 'Ambiente')]//select"))
    name_input.send_keys(company_name)
    rnc_input.send_keys(company_rnc)
    env_select.select_by_value("certecf")
    record_step(driver, "admin_company_modal_filled")
    driver.find_element(By.XPATH, "//button[normalize-space()='Crear']").click()

    WebDriverWait(driver, 20).until(
        EC.invisibility_of_element_located(
            (By.XPATH, "//div[contains(@class, 'fixed') and .//button[normalize-space()='Cancelar']]")
        )
    )
    new_company_link = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.LINK_TEXT, company_name)))
    record_step(driver, "admin_company_created")
    new_company_link.click()

    WebDriverWait(driver, 20).until(EC.url_contains("/companies/"))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, f"//h1[contains(., '{company_name}')]")))
    detail_text = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, f"//*[contains(., '{company_rnc}')]"))
    )
    record_step(driver, "admin_company_detail_open")
    assert company_rnc in detail_text.text
