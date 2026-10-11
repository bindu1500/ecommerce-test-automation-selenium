"""
ShopLite - a small e-commerce web app used as the System Under Test (SUT).

It is deliberately simple so the test framework is the star of the project,
but it covers the flows every real store has: login, search, cart, coupons,
checkout, stock control and order history - all backed by a SQL database.

Two defects are seeded on purpose (see docs/bug_reports.md):
  SHOP-101  Product search is case-sensitive
  SHOP-102  Order total saved to the database ignores the coupon discount
"""
import os
import re
import sqlite3
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
SCHEMA = BASE_DIR / "schema.sql"
SEED = BASE_DIR / "seed.sql"

COUPONS = {
    # code: (type, value, min_subtotal_cents, active)
    "SAVE10": ("percent", 10, 0, True),
    "FLAT50": ("fixed", 5000, 20000, True),
    "OLD20": ("percent", 20, 0, False),
}


def init_db(db_path: str) -> None:
    """Create a fresh database with schema + seed data."""
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA.read_text())
    con.executescript(SEED.read_text())
    con.commit()
    con.close()


def money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def create_app(db_path: str) -> Flask:
    app = Flask(__name__)
    app.secret_key = "shoplite-demo-secret"
    app.config["DB_PATH"] = db_path
    app.jinja_env.filters["money"] = money

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB_PATH"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_):
        con = g.pop("db", None)
        if con is not None:
            con.close()

    def login_required(view):
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        wrapper.__name__ = view.__name__
        return wrapper

    def cart_summary():
        cart = session.get("cart", {})
        items, subtotal = [], 0
        for pid, qty in cart.items():
            p = db().execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
            if p:
                line = p["price_cents"] * qty
                subtotal += line
                items.append({"product": p, "qty": qty, "line": line})
        discount = 0
        code = session.get("coupon")
        if code in COUPONS:
            kind, value, _, _ = COUPONS[code]
            discount = subtotal * value // 100 if kind == "percent" else min(value, subtotal)
        return items, subtotal, discount, subtotal - discount

    # ---------- Auth ----------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not email or not password:
                error = "Email and password are required"
            else:
                u = db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
                if u is None or u["password"] != password:
                    error = "Invalid email or password"
                elif u["is_locked"]:
                    error = "Your account is locked. Contact support."
                else:
                    session.clear()
                    session["user_id"] = u["id"]
                    session["user_name"] = u["full_name"]
                    return redirect(url_for("products"))
        return render_template("login.html", error=error)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---------- Catalogue ----------
    @app.route("/")
    @login_required
    def products():
        q = request.args.get("q", "").strip()
        rows = db().execute("SELECT * FROM products ORDER BY id").fetchall()
        if q:
            # SHOP-101 (seeded defect): case-sensitive match
            rows = [r for r in rows if q in r["name"]]
        return render_template("products.html", products=rows, q=q,
                               message=session.pop("flash", None))

    @app.route("/cart/add/<int:pid>", methods=["POST"])
    @login_required
    def add_to_cart(pid):
        p = db().execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        try:
            qty = int(request.form.get("qty", 1))
        except ValueError:
            qty = 0
        cart = session.get("cart", {})
        new_qty = cart.get(str(pid), 0) + qty
        if p is None:
            session["flash"] = "Product not found"
        elif qty < 1:
            session["flash"] = "Quantity must be at least 1"
        elif new_qty > p["stock"]:
            session["flash"] = f"Only {p['stock']} left in stock"
        else:
            cart[str(pid)] = new_qty
            session["cart"] = cart
            session["flash"] = f"Added {p['name']} to cart"
        return redirect(url_for("products"))

    # ---------- Cart ----------
    @app.route("/cart")
    @login_required
    def cart():
        items, subtotal, discount, total = cart_summary()
        return render_template("cart.html", items=items, subtotal=subtotal,
                               discount=discount, total=total,
                               coupon=session.get("coupon"),
                               message=session.pop("flash", None))

    @app.route("/cart/remove/<pid>", methods=["POST"])
    @login_required
    def remove_from_cart(pid):
        cart = session.get("cart", {})
        cart.pop(pid, None)
        session["cart"] = cart
        if not cart:
            session.pop("coupon", None)
        return redirect(url_for("cart"))

    @app.route("/cart/coupon", methods=["POST"])
    @login_required
    def apply_coupon():
        code = request.form.get("code", "").strip().upper()
        _, subtotal, _, _ = cart_summary()
        if code not in COUPONS:
            session["flash"] = "Invalid coupon code"
        else:
            _, _, minimum, active = COUPONS[code]
            if not active:
                session["flash"] = "This coupon has expired"
            elif subtotal < minimum:
                session["flash"] = f"Coupon requires a minimum order of {money(minimum)}"
            else:
                session["coupon"] = code
                session["flash"] = f"Coupon {code} applied"
        return redirect(url_for("cart"))

    # ---------- Checkout ----------
    @app.route("/checkout", methods=["GET", "POST"])
    @login_required
    def checkout():
        items, subtotal, discount, total = cart_summary()
        if not items:
            return redirect(url_for("cart"))
        errors = []
        if request.method == "POST":
            name = request.form.get("full_name", "").strip()
            address = request.form.get("address", "").strip()
            zip_code = request.form.get("zip", "").strip()
            if not name:
                errors.append("Full name is required")
            if not address:
                errors.append("Address is required")
            if not re.fullmatch(r"\d{5}", zip_code):
                errors.append("ZIP code must be 5 digits")
            if not errors:
                con = db()
                cur = con.execute(
                    "INSERT INTO orders (user_id, ship_name, ship_address, ship_zip,"
                    " subtotal_cents, discount_cents, total_cents, coupon_code, status)"
                    " VALUES (?,?,?,?,?,?,?,?, 'PLACED')",
                    # SHOP-102 (seeded defect): total saved as subtotal, discount ignored
                    (session["user_id"], name, address, zip_code,
                     subtotal, discount, subtotal, session.get("coupon")),
                )
                order_id = cur.lastrowid
                for it in items:
                    p = it["product"]
                    con.execute(
                        "INSERT INTO order_items (order_id, product_id, quantity, unit_price_cents)"
                        " VALUES (?,?,?,?)", (order_id, p["id"], it["qty"], p["price_cents"]))
                    con.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                                (it["qty"], p["id"]))
                con.commit()
                session.pop("cart", None)
                session.pop("coupon", None)
                return redirect(url_for("confirmation", order_id=order_id, paid=total))
        return render_template("checkout.html", items=items, subtotal=subtotal,
                               discount=discount, total=total, errors=errors)

    @app.route("/order/<int:order_id>")
    @login_required
    def confirmation(order_id):
        paid = int(request.args.get("paid", 0))
        return render_template("confirmation.html", order_id=order_id, paid=paid)

    @app.route("/orders")
    @login_required
    def orders():
        rows = db().execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
            (session["user_id"],)).fetchall()
        return render_template("orders.html", orders=rows)

    return app


if __name__ == "__main__":
    path = str(BASE_DIR / "shoplite.db")
    init_db(path)
    create_app(path).run(port=5000, debug=False)
