from selenium.webdriver.common.by import By

from pages.base_page import BasePage, testid


class LoginPage(BasePage):
    PATH = "/login"
    EMAIL = (By.ID, "email")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.ID, "login-btn")
    ERROR = testid("login-error")
    WELCOME = testid("welcome")

    def login(self, email, password):
        self.type(self.EMAIL, email)
        self.type(self.PASSWORD, password)
        self.submit(self.SUBMIT)

    def error_message(self) -> str:
        return self.text_of(self.ERROR)

    def welcome_text(self) -> str:
        return self.text_of(self.WELCOME)
