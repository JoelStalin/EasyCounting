from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from e2e.support import record_step, wait_for_ready


def test_corporate_site_products_and_accounting_management(driver, corporate_url):
    driver.get(corporate_url)
    wait_for_ready(driver)
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'GetUpSoft')]")))
    record_step(driver, "corporate_home_loaded")

    driver.find_element(By.LINK_TEXT, "Productos").click()
    WebDriverWait(driver, 20).until(EC.url_contains("/productos"))
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Accounting Management')]"))
    )
    record_step(driver, "corporate_products_open")

    driver.find_element(
        By.XPATH,
        "//article[.//h2[contains(., 'Accounting Management')]]//a[contains(., 'Ver detalle')]",
    ).click()
    WebDriverWait(driver, 20).until(EC.url_contains("/productos/accounting-management"))
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Gestion contable y cumplimiento fiscal')]"))
    )
    record_step(driver, "corporate_accounting_management_open")

    admin_cta = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, 'admin.getupsoft.com.do/login')]"))
    )
    client_cta = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, 'cliente.getupsoft.com.do/login')]"))
    )
    seller_cta = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//a[contains(@href, 'socios.getupsoft.com.do/login')]"))
    )
    assert admin_cta.is_displayed()
    assert client_cta.is_displayed()
    assert seller_cta.is_displayed()
    record_step(driver, "corporate_ctas_visible")
