from selenium.webdriver.common.by import By

from pages.base_page import BasePage, testid


class CartPage(BasePage):
    PATH = "/cart"
    ROW = testid("cart-row")
    EMPTY = testid("empty-cart")
    COUPON = (By.ID, "coupon")
    APPLY = (By.ID, "apply-coupon")
    SUBTOTAL = testid("subtotal")
    DISCOUNT = testid("discount")
    TOTAL = testid("total")
    CHECKOUT = (By.ID, "checkout-btn")

    def rows(self) -> list[dict]:
        out = []
        for r in self.find_all(self.ROW):
            out.append({
                "sku": r.get_attribute("data-sku"),
                "name": r.find_element(*testid("row-name")).text.strip(),
                "qty": int(r.find_element(*testid("row-qty")).text),
                "line": self.to_cents(r.find_element(*testid("row-total")).text),
            })
        return out

    def is_empty(self) -> bool:
        return self.is_present(self.EMPTY)

    def remove(self, sku):
        row = self.find((By.CSS_SELECTOR, f'[data-testid="cart-row"][data-sku="{sku}"]'))
        self.submit(row.find_element(*testid("remove-item")))

    def apply_coupon(self, code):
        self.type(self.COUPON, code)
        self.submit(self.APPLY)

    def subtotal(self) -> int:
        return self.to_cents(self.text_of(self.SUBTOTAL))

    def discount(self) -> int:
        return self.to_cents(self.text_of(self.DISCOUNT))

    def total(self) -> int:
        return self.to_cents(self.text_of(self.TOTAL))

    def go_to_checkout(self):
        self.submit(self.CHECKOUT)
