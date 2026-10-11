"""Checkout end-to-end tests with SQL back-end validation - TC-CHK-xx"""
import pytest

from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage, ConfirmationPage, OrdersPage


def fill_cart(products_page, base_url, items, coupon=None):
    for sku, qty in items:
        products_page.add_to_cart(sku, qty)
    cart = CartPage(products_page.driver, base_url).open()
    if coupon:
        cart.apply_coupon(coupon)
    cart.go_to_checkout()
    return CheckoutPage(products_page.driver, base_url)


@pytest.mark.smoke
@pytest.mark.db
def test_end_to_end_order_persisted(logged_in, base_url, db):
    """TC-CHK-01: place an order, then verify orders, order_items and stock in SQL."""
    stock_before = {s: db.stock_of(s) for s in ("HDP-002", "CBL-007")}
    checkout = fill_cart(logged_in, base_url, [("HDP-002", 1), ("CBL-007", 3)])
    checkout.place_order(name="Alice Johnson", address="123 Main St, Las Vegas NV", zip_code="89101")

    confirm = ConfirmationPage(logged_in.driver, base_url)
    assert "order is placed" in confirm.text_of(confirm.TITLE)
    order_id = confirm.order_id()

    order = db.order(order_id)
    assert order["status"] == "PLACED"
    assert order["ship_zip"] == "89101"
    assert order["subtotal_cents"] == 8999 + 3 * 999
    assert order["total_cents"] == confirm.amount_paid()
    assert db.order_items(order_id) == [
        {"sku": "CBL-007", "quantity": 3, "unit_price_cents": 999},
        {"sku": "HDP-002", "quantity": 1, "unit_price_cents": 8999},
    ]
    assert db.stock_of("HDP-002") == stock_before["HDP-002"] - 1
    assert db.stock_of("CBL-007") == stock_before["CBL-007"] - 3


def test_order_appears_in_history(logged_in, base_url):
    """TC-CHK-02: new order is listed on the Orders page."""
    fill_cart(logged_in, base_url, [("MSE-003", 1)]).place_order()
    order_id = ConfirmationPage(logged_in.driver, base_url).order_id()
    assert order_id in OrdersPage(logged_in.driver, base_url).open().order_ids()


def test_cart_cleared_after_order(logged_in, base_url):
    """TC-CHK-03: cart is empty after a successful order."""
    fill_cart(logged_in, base_url, [("MSE-003", 1)]).place_order()
    cart = CartPage(logged_in.driver, base_url).open()
    assert cart.is_empty() and cart.cart_count() == 0


@pytest.mark.parametrize("name, address, zip_code, expected_error", [
    ("", "1 Main St", "89101", "Full name is required"),
    ("Alice", "", "89101", "Address is required"),
    ("Alice", "1 Main St", "8910", "ZIP code must be 5 digits"),
    ("Alice", "1 Main St", "89A01", "ZIP code must be 5 digits"),
])
@pytest.mark.db
def test_checkout_validation_blocks_order(logged_in, base_url, db, name, address, zip_code, expected_error):
    """TC-CHK-04..07: invalid shipping details are rejected and NO order row is written."""
    checkout = fill_cart(logged_in, base_url, [("MSE-003", 1)])
    checkout.place_order(name=name, address=address, zip_code=zip_code)
    assert expected_error in checkout.errors()
    assert db.order_count() == 0
    assert db.stock_of("MSE-003") == 50


@pytest.mark.db
def test_users_only_see_their_own_orders(driver, base_url, db):
    """TC-CHK-08: data isolation - Bob cannot see Alice's orders."""
    from pages.login_page import LoginPage
    from pages.products_page import ProductsPage

    login = LoginPage(driver, base_url).open()
    login.login("alice@shoplite.test", "Passw0rd!")
    fill_cart(ProductsPage(driver, base_url), base_url, [("MSE-003", 1)]).place_order()
    alice_order = ConfirmationPage(driver, base_url).order_id()

    login.logout()
    login.open().login("bob@shoplite.test", "Passw0rd!")
    assert alice_order not in OrdersPage(driver, base_url).open().order_ids()
    assert db.scalar("SELECT COUNT(*) FROM orders WHERE user_id = 2") == 0


@pytest.mark.db
@pytest.mark.known_bug
@pytest.mark.xfail(reason="SHOP-102: orders.total_cents ignores coupon discount", strict=True)
def test_discounted_total_saved_to_database(logged_in, base_url, db):
    """TC-CHK-09: amount paid on screen must equal total_cents stored in SQL."""
    checkout = fill_cart(logged_in, base_url, [("HDP-002", 2)], coupon="SAVE10")
    ui_total = checkout.total()
    checkout.place_order()
    order = db.order(ConfirmationPage(logged_in.driver, base_url).order_id())
    assert order["discount_cents"] == 1799
    assert order["total_cents"] == ui_total == order["subtotal_cents"] - order["discount_cents"]
