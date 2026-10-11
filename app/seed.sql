INSERT INTO users (email, password, full_name, is_locked) VALUES
    ('alice@shoplite.test', 'Passw0rd!', 'Alice Johnson', 0),
    ('bob@shoplite.test',   'Passw0rd!', 'Bob Smith',     0),
    ('locked@shoplite.test','Passw0rd!', 'Larry Locked',  1);

INSERT INTO products (sku, name, category, price_cents, stock) VALUES
    ('LAP-001', 'Laptop Pro 14',          'Electronics', 129999, 5),
    ('HDP-002', 'Wireless Headphones',    'Electronics',   8999, 20),
    ('MSE-003', 'Ergonomic Mouse',        'Accessories',   2499, 50),
    ('KBD-004', 'Mechanical Keyboard',    'Accessories',   7999, 15),
    ('MON-005', '27in 4K Monitor',        'Electronics',  32999, 3),
    ('BAG-006', 'Laptop Backpack',        'Accessories',   4999, 0),
    ('CBL-007', 'USB-C Cable 2m',         'Accessories',    999, 100),
    ('STD-008', 'Adjustable Laptop Stand','Accessories',   3499, 8);
