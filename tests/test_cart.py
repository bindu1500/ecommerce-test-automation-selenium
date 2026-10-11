"""Shopping cart and coupon tests - TC-CART-xx"""
import pytest

from pages.cart_page import CartPage


@pytest.fixture
def cart(logged_in, base_url):
    return CartPage(logged_in.driver, base_url)


@pytest.mark.smoke
def test_add_single_item(logged_in, cart):
    """TC-CART-01: adding an item updates the badge and the cart line."""
    logged_in.add_to_cart("MSE-003", qty=2)
    assert logged_in.flash_message() == "Added Ergonomic Mouse to cart"
    assert logged_in.cart_count() == 2
    cart.open()
    assert cart.rows() == [{"sku": "MSE-003", "name": "Ergonomic Mouse", "qty": 2, "line": 4998}]


def test_adding_same_item_twice_merges_quantity(logged_in, cart):
    """TC-CART-02: same product added twice becomes one line with combined qty."""
    logged_in.add_to_cart("CBL-007", qty=1)
    logged_in.add_to_cart("CBL-007", qty=3)
    cart.open()
    rows = cart.rows()
    assert len(rows) == 1 and rows[0]["qty"] == 4


def test_cart_totals_are_correct(logged_in, cart):
    """TC-CART-03: line totals and subtotal add up (math checked independently)."""
    logged_in.add_to_cart("HDP-002", qty=1)   # 89.99
    logged_in.add_to_cart("KBD-004", qty=2)   # 2 x 79.99
    cart.open()
    assert sum(r["line"] for r in cart.rows()) == cart.subtotal() == 8999 + 2 * 7999
    assert cart.total() == cart.subtotal()


@pytest.mark.parametrize("qty, message", [
    (0, "Quantity must be at least 1"),
    (-2, "Quantity must be at least 1"),
    (4, "Only 3 left in stock"),
])
def test_invalid_quantity_rejected(logged_in, cart, qty, message):
    """TC-CART-04..06: boundary values for quantity (0, negative, stock + 1)."""
    logged_in.add_to_cart("MON-005", qty=qty)
    assert logged_in.flash_message() == message
    assert logged_in.cart_count() == 0


def test_quantity_equal_to_stock_allowed(logged_in):
    """TC-CART-07: boundary - buying the exact remaining stock is allowed."""
    logged_in.add_to_cart("MON-005", qty=3)
    assert logged_in.cart_count() == 3


def test_remove_item_empties_cart(logged_in, cart):
    """TC-CART-08: removing the only item shows the empty cart state."""
    logged_in.add_to_cart("MSE-003")
    cart.open()
    cart.remove("MSE-003")
    assert cart.is_empty()


@pytest.mark.smoke
def test_percent_coupon(logged_in, cart):
    """TC-CART-09: SAVE10 takes 10% off the subtotal."""
    logged_in.add_to_cart("HDP-002", qty=2)  # 179.98
    cart.open()
    cart.apply_coupon("save10")              # lower-case on purpose
    assert cart.flash_message() == "Coupon SAVE10 applied"
    assert cart.discount() == 17998 // 10
    assert cart.total() == cart.subtotal() - cart.discount()


def test_fixed_coupon_requires_minimum(logged_in, cart):
    """TC-CART-10: FLAT50 is refused below $200 and accepted above it."""
    logged_in.add_to_cart("HDP-002")          # 89.99 - below minimum
    cart.open()
    cart.apply_coupon("FLAT50")
    assert cart.flash_message() == "Coupon requires a minimum order of $200.00"
    assert cart.discount() == 0

    logged_in.open().add_to_cart("MON-005")   # +329.99 - now above
    cart.open()
    cart.apply_coupon("FLAT50")
    assert cart.discount() == 5000


@pytest.mark.parametrize("code, message", [
    ("OLD20", "This coupon has expired"),
    ("FREESTUFF", "Invalid coupon code"),
    ("", "Invalid coupon code"),
])
def test_bad_coupons_rejected(logged_in, cart, code, message):
    """TC-CART-11..13: expired, unknown and blank coupons."""
    logged_in.add_to_cart("MSE-003")
    cart.open()
    cart.apply_coupon(code)
    assert cart.flash_message() == message
    assert cart.discount() == 0
