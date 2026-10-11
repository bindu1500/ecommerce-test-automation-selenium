-- ShopLite data validation queries
-- Run after any test cycle or deployment. Every query should return ZERO rows.
-- Usage: sqlite3 reports/test_shoplite_0.db < sql/data_validation.sql

-- DV-01  Negative stock (overselling)
SELECT 'DV-01 negative stock' AS check_name, sku, stock
FROM products WHERE stock < 0;

-- DV-02  Duplicate SKUs
SELECT 'DV-02 duplicate sku' AS check_name, sku, COUNT(*) AS copies
FROM products GROUP BY sku HAVING COUNT(*) > 1;

-- DV-03  Emails not stored in lower case (breaks case-insensitive login)
SELECT 'DV-03 email case' AS check_name, email
FROM users WHERE email <> LOWER(email);

-- DV-04  Orphan order lines (no parent order or product)
SELECT 'DV-04 orphan order_item' AS check_name, oi.id
FROM order_items oi
LEFT JOIN orders o   ON o.id = oi.order_id
LEFT JOIN products p ON p.id = oi.product_id
WHERE o.id IS NULL OR p.id IS NULL;

-- DV-05  Order subtotal does not equal the sum of its lines
SELECT 'DV-05 subtotal mismatch' AS check_name, o.id, o.subtotal_cents,
       SUM(oi.quantity * oi.unit_price_cents) AS items_sum
FROM orders o JOIN order_items oi ON oi.order_id = o.id
GROUP BY o.id HAVING o.subtotal_cents <> items_sum;

-- DV-06  Order total does not equal subtotal minus discount   (catches SHOP-102)
SELECT 'DV-06 total mismatch' AS check_name, id, subtotal_cents, discount_cents, total_cents
FROM orders WHERE total_cents <> subtotal_cents - discount_cents;

-- DV-07  Orders with no line items
SELECT 'DV-07 empty order' AS check_name, o.id
FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.id
WHERE oi.id IS NULL;

-- DV-08  Discount recorded without a coupon code
SELECT 'DV-08 discount without coupon' AS check_name, id, discount_cents
FROM orders WHERE discount_cents > 0 AND coupon_code IS NULL;
