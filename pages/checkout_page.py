from selenium.webdriver.common.by import By

from pages.base_page import BasePage, testid


class CheckoutPage(BasePage):
    PATH = "/checkout"
    NAME = (By.ID, "full_name")
    ADDRESS = (By.ID, "address")
    ZIP = (By.ID, "zip")
    PLACE = (By.ID, "place-order")
    ERRORS = testid("checkout-error")
    TOTAL = testid("checkout-total")

    def place_order(self, name="Alice Johnson", address="123 Main St, Las Vegas NV", zip_code="89101"):
        if name:
            self.type(self.NAME, name)
        if address:
            self.type(self.ADDRESS, address)
        if zip_code:
            self.type(self.ZIP, zip_code)
        self.submit(self.PLACE)

    def errors(self) -> list[str]:
        return [e.text.strip() for e in self.find_all(self.ERRORS)]

    def total(self) -> int:
        return self.to_cents(self.text_of(self.TOTAL))


class ConfirmationPage(BasePage):
    TITLE = testid("confirm-title")
    ORDER_ID = testid("order-id")
    PAID = testid("amount-paid")

    def order_id(self) -> int:
        return int(self.text_of(self.ORDER_ID))

    def amount_paid(self) -> int:
        return self.to_cents(self.text_of(self.PAID))


class OrdersPage(BasePage):
    PATH = "/orders"
    ROW = testid("order-row")

    def order_ids(self) -> list[int]:
        return [int(r.get_attribute("data-order-id")) for r in self.find_all(self.ROW)]
