from selenium.webdriver.common.by import By

from pages.base_page import BasePage, testid


class ProductsPage(BasePage):
    PATH = "/"
    SEARCH = (By.ID, "search")
    SEARCH_BTN = (By.ID, "search-btn")
    CARD = testid("product-card")
    NAME = testid("product-name")
    NO_RESULTS = testid("no-results")

    def search(self, term):
        self.type(self.SEARCH, term)
        self.submit(self.SEARCH_BTN)

    def product_names(self) -> list[str]:
        return [e.text.strip() for e in self.find_all(self.NAME)]

    def has_no_results(self) -> bool:
        return self.is_present(self.NO_RESULTS)

    def _card(self, sku):
        return self.find((By.CSS_SELECTOR, f'[data-testid="product-card"][data-sku="{sku}"]'))

    def price_of(self, sku) -> int:
        return self.to_cents(self._card(sku).find_element(*testid("product-price")).text)

    def stock_text(self, sku) -> str:
        return self._card(sku).find_element(*testid("product-stock")).text.strip()

    def add_button_enabled(self, sku) -> bool:
        return self._card(sku).find_element(*testid("add-to-cart")).is_enabled()

    def add_to_cart(self, sku, qty=1):
        card = self._card(sku)
        qty_input = card.find_element(*testid("qty-input"))
        qty_input.clear()
        qty_input.send_keys(str(qty))
        self.submit(card.find_element(*testid("add-to-cart")))
