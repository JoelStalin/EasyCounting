from automation.browser.config import BrowserAutomationSettings


def test_browser_settings_from_app_settings() -> None:
    config = BrowserAutomationSettings.from_settings()
    assert config.mode in {"assistive", "fallback", "evidence-only"}
