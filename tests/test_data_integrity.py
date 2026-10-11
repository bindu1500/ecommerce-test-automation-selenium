"""
Pure SQL data-quality checks - TC-DB-xx.
These run without a browser and catch problems the UI can hide.
The same queries live in sql/data_validation.sql for manual use.
"""
import pytest

pytestmark = pytest.mark.db


def test_no_negative_stock(db):
    """TC-DB-01"""
    assert db.query("SELECT sku, stock FROM products WHERE stock < 0") == []


def test_skus_are_unique(db):
    """TC-DB-02"""
    assert db.query("SELECT sku, COUNT(*) c FROM products GROUP BY sku HAVING c > 1") == []


def test_user_emails_unique_and_lowercase(db):
    """TC-DB-03"""
    assert db.query("SELECT email FROM users WHERE email <> LOWER(email)") == []
    assert db.query("SELECT email, COUNT(*) c FROM users GROUP BY email HAVING c > 1") == []


def test_no_orphan_order_items(db):
    """TC-DB-04: every order_item points at an existing order and product."""
    orphans = db.query("""
        SELECT oi.id FROM order_items oi
        LEFT JOIN orders o   ON o.id = oi.order_id
        LEFT JOIN products p ON p.id = oi.product_id
        WHERE o.id IS NULL OR p.id IS NULL""")
    assert orphans == []


def test_order_subtotal_matches_line_items(logged_in, base_url, db):
    """TC-DB-05: orders.subtotal_cents = SUM(quantity * unit_price) after a real UI order."""
    from tests.test_checkout import fill_cart
    fill_cart(logged_in, base_url, [("KBD-004", 2), ("MSE-003", 1)]).place_order()
    mismatches = db.query("""
        SELECT o.id, o.subtotal_cents, SUM(oi.quantity * oi.unit_price_cents) AS items_sum
        FROM orders o JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.id HAVING o.subtotal_cents <> items_sum""")
    assert db.order_count() == 1
    assert mismatches == []
