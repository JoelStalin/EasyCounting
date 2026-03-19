from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from e2e.support import dismiss_tour, ensure_tour_visible, record_step, wait_for_ready


def test_seller_login_emit_demo_open_clients_and_logout(driver, seller_url):
    driver.get(f"{seller_url}/emit/ecf")
    wait_for_ready(driver)
    record_step(driver, "seller_redirect_to_login")

    WebDriverWait(driver, 20).until(EC.url_contains("/login"))
    email = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "email")))
    password = driver.find_element(By.ID, "password")
    email.send_keys("seller@getupsoft.com.do")
    password.send_keys("Seller123!")
    record_step(driver, "seller_login_form_filled")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 20).until(EC.url_contains("/emit/ecf"))
    tenant_select = Select(WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "tenantId"))))
    tenant_select.select_by_index(1)
    ensure_tour_visible(driver, "Este flujo genera comprobantes demo solo para tenants asignados.")
    record_step(driver, "seller_tour_open")
    dismiss_tour(driver)
    record_step(driver, "seller_tour_dismissed")
    record_step(driver, "seller_emit_form_ready")
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].form.requestSubmit()", submit_button)

    success = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Comprobante seller generado en modo demo')]"))
    )
    record_step(driver, "seller_emit_success")
    assert "demo" in success.text.lower()

    driver.get(f"{seller_url}/clients")
    WebDriverWait(driver, 20).until(EC.url_contains("/clients"))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'Clientes asignados')]")))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Empresa Demo')]")))
    record_step(driver, "seller_clients_open")

    driver.get(f"{seller_url}/profile")
    WebDriverWait(driver, 20).until(EC.url_contains("/profile"))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'Perfil del socio')]")))
    record_step(driver, "seller_profile_open")

    logout_button = driver.find_element(By.XPATH, "//button[contains(., 'Salir')]")
    driver.execute_script("arguments[0].click()", logout_button)
    WebDriverWait(driver, 20).until(EC.url_contains("/login"))
    record_step(driver, "seller_logout_done")


def test_seller_auditor_cannot_access_emit(driver, seller_url):
    driver.get(f"{seller_url}/emit/ecf")
    wait_for_ready(driver)
    record_step(driver, "seller_auditor_redirect_to_login")

    WebDriverWait(driver, 20).until(EC.url_contains("/login"))
    email = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "email")))
    password = driver.find_element(By.ID, "password")
    email.send_keys("seller.auditor@getupsoft.com.do")
    password.send_keys("SellerAudit123!")
    record_step(driver, "seller_auditor_login_form_filled")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 20).until(EC.url_contains("/emit/ecf"))
    forbidden = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'Acceso restringido')]"))
    )
    record_step(driver, "seller_auditor_forbidden_emit")
    assert "Acceso restringido" in forbidden.text
