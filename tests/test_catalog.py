"""Catalogue and search tests - TC-CAT-xx"""
import pytest


@pytest.mark.smoke
def test_all_products_listed(logged_in, db):
    """TC-CAT-01: UI shows exactly the products stored in the database, in order."""
    expected = [r["name"] for r in db.query("SELECT name FROM products ORDER BY id")]
    assert logged_in.product_names() == expected


@pytest.mark.db
def test_ui_prices_match_database(logged_in, db):
    """TC-CAT-02: every price on screen equals price_cents in the products table."""
    for row in db.query("SELECT sku, price_cents FROM products"):
        assert logged_in.price_of(row["sku"]) == row["price_cents"], row["sku"]


def test_out_of_stock_product_cannot_be_added(logged_in):
    """TC-CAT-03: a product with stock = 0 shows 'Out of stock' and a disabled button."""
    assert logged_in.stock_text("BAG-006") == "Out of stock"
    assert not logged_in.add_button_enabled("BAG-006")


@pytest.mark.parametrize("term, expected", [
    ("Laptop", ["Laptop Pro 14", "Laptop Backpack", "Adjustable Laptop Stand"]),
    ("Mouse", ["Ergonomic Mouse"]),
    ("4K", ["27in 4K Monitor"]),
])
def test_search_returns_matching_products(logged_in, term, expected):
    """TC-CAT-04..06: search by keyword."""
    logged_in.search(term)
    assert sorted(logged_in.product_names()) == sorted(expected)


def test_search_with_no_match_shows_message(logged_in):
    """TC-CAT-07: unknown keyword shows the empty state."""
    logged_in.search("toaster")
    assert logged_in.has_no_results()
    assert logged_in.product_names() == []


@pytest.mark.known_bug
@pytest.mark.xfail(reason="SHOP-101: product search is case-sensitive", strict=True)
def test_search_is_case_insensitive(logged_in):
    """TC-CAT-08: 'laptop' should find the same products as 'Laptop'."""
    logged_in.search("laptop")
    assert len(logged_in.product_names()) == 3
