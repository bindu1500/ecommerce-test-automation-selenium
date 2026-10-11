# Test Plan — ShopLite E-Commerce

## 1. Objective
Verify that a customer can find products, build a cart, apply coupons and place an order,
and that every order is stored correctly in the SQL database.

## 2. Scope
| In scope | Out of scope |
|---|---|
| Login / logout, session protection | Payment gateway (not in app) |
| Catalogue, search, stock display | Performance / load testing |
| Cart, quantity rules, coupons | Mobile native apps |
| Checkout validation, order creation | Cross-browser beyond Chrome |
| Database integrity (orders, stock, keys) | |

## 3. Approach
- **UI automation**: Selenium 4 + Python, Page Object Model, explicit waits only.
- **Back-end validation**: every money/stock-related UI test is followed by SQL assertions.
- **Techniques**: equivalence partitioning, boundary value analysis (qty 0 / −2 / stock / stock+1,
  ZIP 4 digits / letters, coupon minimum), negative testing, security checks (SQL injection, auth bypass, data isolation).
- **Data-driven**: login negatives come from `testdata/login_data.json`; other matrices use `pytest.mark.parametrize`.
- **Isolation**: database re-seeded and a new browser created for every test → tests run in any order or in parallel.

## 4. Test levels and suites
| Marker | Purpose | When it runs |
|---|---|---|
| `smoke` | 6 critical-path tests | Every push (CI job 1) |
| full suite | 45 tests | Every push to main / PR (CI job 2) |
| `db` | SQL-backed checks | Included in full suite |
| `known_bug` | Open Jira defects (xfail strict) | Included; turns red when bug is fixed |

## 5. Entry / exit criteria
- **Entry**: app starts, seed data loaded, smoke suite passes.
- **Exit**: 100% of non-`known_bug` tests pass; every failure has a Jira ticket; no open High/Highest defect without sign-off.

## 6. Defect management
Defects logged in Jira with steps, expected/actual, environment, severity and the automated test that found them
(see `bug_reports.md`). Each defect gets a regression test before it is closed.

## 7. Traceability
`test_cases.csv` maps every Test ID → automated test function. It imports directly into Jira (Xray/Zephyr) via CSV import.

## 8. Results (latest run)
| Total | Passed | Expected failures (open bugs) | Failed |
|---|---|---|---|
| 45 | 43 | 2 (SHOP-101, SHOP-102) | 0 |
