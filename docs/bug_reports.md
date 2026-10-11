# Defect Log (Jira format)

Both defects were found by the automated suite. Each one has a regression test marked
`@pytest.mark.xfail(strict=True)`, so the build stays green while the bug is open and
**turns red the moment a developer fixes it** – a reminder to remove the marker and close the ticket.

---

## SHOP-101 — Product search is case-sensitive

| Field | Value |
|---|---|
| Issue type | Bug |
| Priority | Medium |
| Severity | S3 – Major (feature works, but wrong results) |
| Component | Catalogue / Search |
| Environment | ShopLite build local, Chrome 141 headless, Python 3.13 |
| Found by | `tests/test_catalog.py::test_search_is_case_insensitive` (TC-CAT-08) |
| Labels | `search`, `automation-found`, `regression` |

**Steps to reproduce**
1. Log in as `alice@shoplite.test` / `Passw0rd!`
2. Type `laptop` (lower case) in the search box and press **Search**

**Expected result**
3 products returned: Laptop Pro 14, Laptop Backpack, Adjustable Laptop Stand (same as searching `Laptop`).

**Actual result**
"No products found". Automated assertion: `assert 0 == 3`.

**Root cause (from code review)**
`store.py` filters with `q in r["name"]`, a case-sensitive Python string match.

**Suggested fix**
Compare lower-cased values, or push the filter into SQL with `LIKE` / `COLLATE NOCASE`.

**Business impact**
Most shoppers type in lower case on mobile; they will believe items are unavailable → lost sales.

---

## SHOP-102 — Order total saved to database ignores coupon discount

| Field | Value |
|---|---|
| Issue type | Bug |
| Priority | **High** |
| Severity | S2 – Critical (financial data incorrect) |
| Component | Checkout / Orders DB |
| Environment | ShopLite build local, SQLite, Chrome 141 headless |
| Found by | `tests/test_checkout.py::test_discounted_total_saved_to_database` (TC-CHK-09) and SQL check DV-06 |
| Labels | `checkout`, `data-integrity`, `sql`, `automation-found` |

**Steps to reproduce**
1. Log in as `alice@shoplite.test`
2. Add 2 × Wireless Headphones ($89.99) to cart → subtotal $179.98
3. Apply coupon `SAVE10` → UI shows discount $17.99, total **$161.99**
4. Check out with valid address → confirmation page shows "Amount paid: $161.99"
5. Run: `SELECT subtotal_cents, discount_cents, total_cents FROM orders ORDER BY id DESC LIMIT 1;`

**Expected result**
`total_cents = 16199` (subtotal − discount)

**Actual result**
`subtotal_cents = 17998, discount_cents = 1799, total_cents = 17998`. Automated assertion: `assert 17998 == 16199`.

**Root cause**
The `INSERT INTO orders` statement passes `subtotal` into the `total_cents` column instead of `total`.

**Business impact**
Every discounted order is recorded $X higher than the customer paid. Revenue reports, refunds,
and accounting reconciliation will be wrong. **The UI looks correct, so this is only detectable
with database-level validation** – which is why the suite checks SQL, not just screens.
