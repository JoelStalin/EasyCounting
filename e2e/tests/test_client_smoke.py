from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from e2e.support import record_step, wait_for_ready


def test_client_login_emit_ecf_profile_and_logout(driver, client_url):
    driver.get(f"{client_url}/emit/ecf")
    wait_for_ready(driver)
    record_step(driver, "client_redirect_to_login")

    WebDriverWait(driver, 20).until(EC.url_contains("/login"))
    email = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "email")))
    password = driver.find_element(By.ID, "password")
    email.send_keys("cliente@getupsoft.com.do")
    password.send_keys("Tenant123!")
    record_step(driver, "client_login_form_filled")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 20).until(EC.url_contains("/emit/ecf"))
    textarea = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.TAG_NAME, "textarea")))
    record_step(driver, "client_emit_form_ready")
    textarea.send_keys("PHhtbD48ZWNmPkRlbW88L2VjZj48L3htbD4=")
    record_step(driver, "client_emit_payload_loaded")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    success = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'e-CF enviado a DGII')]"))
    )
    record_step(driver, "client_emit_success")
    assert "simulado" in success.text

    driver.find_element(By.LINK_TEXT, "Perfil").click()
    WebDriverWait(driver, 20).until(EC.url_contains("/profile"))
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, "//h1[contains(., 'Perfil')]")))
    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, "//*[contains(., 'cliente@getupsoft.com.do')]"))
    )
    record_step(driver, "client_profile_open")

    driver.find_element(By.XPATH, "//button[contains(., 'Salir')]").click()
    WebDriverWait(driver, 20).until(EC.url_contains("/login"))
    record_step(driver, "client_logout_done")
