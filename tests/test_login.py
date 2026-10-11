"""Authentication tests - TC-LOGIN-xx in docs/test_cases.csv"""
import json
from pathlib import Path

import pytest

from conftest import STANDARD_USER
from pages.login_page import LoginPage
from pages.products_page import ProductsPage

DATA = json.loads((Path(__file__).parents[1] / "testdata" / "login_data.json").read_text())


@pytest.mark.smoke
def test_valid_login_lands_on_products(driver, base_url):
    """TC-LOGIN-01: valid credentials open the catalogue and greet the user."""
    login = LoginPage(driver, base_url).open()
    login.login(STANDARD_USER["email"], STANDARD_USER["password"])
    assert login.welcome_text() == f"Hi, {STANDARD_USER['name']}"
    assert login.current_path == "/"


def test_email_is_case_insensitive(driver, base_url):
    """TC-LOGIN-02: ALICE@SHOPLITE.TEST should log in the same user."""
    login = LoginPage(driver, base_url).open()
    login.login(STANDARD_USER["email"].upper(), STANDARD_USER["password"])
    assert "Alice" in login.welcome_text()


@pytest.mark.parametrize("case", DATA["invalid_logins"], ids=lambda c: c["id"])
def test_invalid_login_shows_error(driver, base_url, case):
    """TC-LOGIN-03..08: negative logins are rejected with the right message (data-driven)."""
    login = LoginPage(driver, base_url).open()
    login.login(case["email"], case["password"])
    assert login.error_message() == case["error"]
    assert login.current_path == "/login"


def test_protected_page_redirects_to_login(driver, base_url):
    """TC-LOGIN-09: unauthenticated access to /cart is redirected to login."""
    driver.get(base_url + "/cart")
    assert LoginPage(driver, base_url).current_path == "/login"


@pytest.mark.smoke
def test_logout_ends_session(logged_in, base_url):
    """TC-LOGIN-10: after logout the back-end session is gone."""
    logged_in.logout()
    driver = logged_in.driver
    driver.get(base_url + "/")
    assert ProductsPage(driver, base_url).current_path == "/login"
