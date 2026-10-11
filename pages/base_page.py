"""Shared helpers every page object inherits: explicit waits, typing, reading text."""
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def testid(value: str):
    """Locator for data-testid attributes - stable and independent of styling."""
    return (By.CSS_SELECTOR, f'[data-testid="{value}"]')


class BasePage:
    PATH = "/"
    FLASH = testid("flash")
    CART_COUNT = testid("cart-count")
    LOGOUT = testid("nav-logout")

    def __init__(self, driver, base_url, timeout=10):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, timeout)

    def open(self):
        self.driver.get(self.base_url + self.PATH)
        return self

    def find(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_all(self, locator):
        return self.driver.find_elements(*locator)

    def click(self, locator):
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def submit(self, locator_or_element):
        """Click something that posts a form, then wait for the new page.
        Waiting for the old <html> to go stale prevents reading the previous page's text."""
        old_html = self.driver.find_element(By.TAG_NAME, "html")
        if isinstance(locator_or_element, tuple):
            self.click(locator_or_element)
        else:
            locator_or_element.click()
        self.wait.until(lambda _: self._is_detached(old_html))
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    @staticmethod
    def _is_detached(element) -> bool:
        # Chrome sometimes reports a detached node as a generic inspector error
        # instead of StaleElementReferenceException, so treat both as "gone".
        try:
            element.is_enabled()
            return False
        except WebDriverException:
            return True

    def type(self, locator, text):
        el = self.find(locator)
        el.clear()
        el.send_keys(text)

    def text_of(self, locator) -> str:
        return self.find(locator).text.strip()

    def is_present(self, locator) -> bool:
        return len(self.driver.find_elements(*locator)) > 0

    def flash_message(self) -> str:
        return self.text_of(self.FLASH)

    def cart_count(self) -> int:
        return int(self.text_of(self.CART_COUNT))

    def logout(self):
        self.submit(self.LOGOUT)

    @property
    def current_path(self) -> str:
        return self.driver.current_url.replace(self.base_url, "").split("?")[0]

    @staticmethod
    def to_cents(price_text: str) -> int:
        """'$1,299.99' -> 129999"""
        return round(float(price_text.replace("$", "").replace(",", "")) * 100)
