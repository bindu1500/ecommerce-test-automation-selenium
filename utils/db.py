"""Thin SQL client used by tests to verify what the UI did actually reached the database."""
import sqlite3


class DbClient:
    def __init__(self, db_path):
        self.db_path = db_path

    def query(self, sql, params=()) -> list[dict]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in con.execute(sql, params).fetchall()]
        finally:
            con.close()

    def scalar(self, sql, params=()):
        rows = self.query(sql, params)
        return next(iter(rows[0].values())) if rows else None

    # --- domain helpers ---
    def stock_of(self, sku) -> int:
        return self.scalar("SELECT stock FROM products WHERE sku = ?", (sku,))

    def order(self, order_id) -> dict:
        rows = self.query("SELECT * FROM orders WHERE id = ?", (order_id,))
        return rows[0] if rows else None

    def order_items(self, order_id) -> list[dict]:
        return self.query(
            "SELECT p.sku, oi.quantity, oi.unit_price_cents "
            "FROM order_items oi JOIN products p ON p.id = oi.product_id "
            "WHERE oi.order_id = ? ORDER BY p.sku", (order_id,))

    def order_count(self) -> int:
        return self.scalar("SELECT COUNT(*) FROM orders")
