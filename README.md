# ShopLite QA — E-Commerce Test Automation Framework

End-to-end test automation for an e-commerce web app using **Selenium 4, Python, Pytest and SQL**,
with Jira-ready test cases and defect reports and a GitHub Actions CI pipeline.

The suite drives the browser **and** checks the database behind it. That is how it caught a
pricing defect (SHOP-102) that looks correct on screen but stores the wrong total in the orders table.

![tests](https://img.shields.io/badge/tests-45-blue) ![passing](https://img.shields.io/badge/passing-43-brightgreen) ![open%20bugs](https://img.shields.io/badge/open%20bugs-2-orange)

---

## What it covers

| Area | Tests | Highlights |
|---|---|---|
| Login & security | 10 | Data-driven negatives from JSON, locked account, SQL injection, auth bypass, logout |
| Catalogue & search | 8 | UI prices vs SQL, out-of-stock state, search matrix |
| Cart & coupons | 13 | Boundary values (qty 0 / −2 / stock / stock+1), coupon minimums, expired codes |
| Checkout | 9 | Full order → verifies `orders`, `order_items`, stock decrement in SQL; user data isolation |
| Data integrity (SQL) | 5 | Orphans, duplicates, negative stock, subtotal = sum of lines |
| **Total** | **45** | 43 pass · 2 expected failures for logged bugs |

## Framework design

```
shopqa/
├── app/                  # System under test: Flask + SQLite store (login, cart, coupons, checkout)
├── pages/                # Page Object Model - one class per page, all locators in one place
│   ├── base_page.py      #   explicit waits, safe form submit (waits for page reload), price parsing
│   ├── login_page.py  products_page.py  cart_page.py  checkout_page.py
├── utils/db.py           # SQL client used to assert on back-end data
├── tests/                # Pytest suites (login, catalog, cart, checkout, data integrity)
├── testdata/             # JSON test data for data-driven tests
├── sql/data_validation.sql   # 8 reusable data-quality queries (every one should return 0 rows)
├── docs/
│   ├── test_plan.md      # Scope, approach, entry/exit criteria, results
│   ├── test_cases.csv    # 45 test cases, Jira CSV-import ready, mapped to automated tests
│   └── bug_reports.md    # SHOP-101, SHOP-102 in Jira format
├── conftest.py           # Fixtures: app server, fresh DB per test, Chrome driver, screenshot on failure
└── .github/workflows/tests.yml   # CI: smoke gate → parallel full regression → HTML report artifact
```

**Key decisions**
- **Page Object Model** — tests read like user stories; a UI change means editing one locator, not 20 tests.
- **`data-testid` locators** — stable against styling/layout changes.
- **Explicit waits only, zero `sleep()`** — and a custom `submit()` that waits for the old page to detach,
  which removed an intermittent stale-element failure seen in early runs.
- **Fresh database + fresh browser per test** — no test depends on another; safe to run in parallel (`pytest -n 4`).
- **UI + SQL assertions together** — the screen can be right while the data is wrong.
- **Known bugs as strict `xfail`** — the build stays green while a bug is open and turns red when it's fixed,
  so the ticket can't be forgotten.
- **Screenshot on failure**, embedded in a self-contained HTML report.

## Run it

```bash
git clone <your-repo-url> && cd shopqa
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest                       # full suite + reports/report.html
pytest -m smoke              # 6 critical-path tests
pytest -m db                 # SQL-backed tests only
pytest -n 4                  # parallel run
pytest --headed -k checkout  # watch the browser
python app/store.py          # explore the app manually at http://127.0.0.1:5000
```

Requires Chrome. Selenium Manager downloads the matching driver automatically.
Optional env vars: `CHROME_BINARY`, `CHROMEDRIVER_PATH`, `APP_PORT`.

Test login: `alice@shoplite.test` / `Passw0rd!` · coupons: `SAVE10`, `FLAT50` (min $200), `OLD20` (expired)

## Defects found

| Key | Summary | Priority | Caught by |
|---|---|---|---|
| SHOP-101 | Product search is case-sensitive | Medium | UI test TC-CAT-08 |
| SHOP-102 | Order total in DB ignores coupon discount (UI shows correct amount) | **High** | SQL assertion TC-CHK-09 + query DV-06 |

Full write-ups with steps, root cause and business impact: [`docs/bug_reports.md`](docs/bug_reports.md)

---

## Resume entry

**E-Commerce Test Automation Framework** | Selenium, Python, Pytest, SQL, Jira, GitHub Actions
- Built a Selenium/Pytest framework using the Page Object Model to automate 45 test cases across login, search, cart, coupons and checkout for an e-commerce web app.
- Added SQL back-end validation to UI tests, uncovering a high-priority defect where discounted orders were saved to the database at full price even though the UI showed the correct total.
- Applied boundary-value, negative and security testing (SQL injection, auth bypass, cross-user data isolation) using data-driven tests from JSON and parametrized matrices.
- Wrote a test plan, 45 Jira-importable test cases with traceability to automated tests, and Jira-format defect reports with root cause and business impact.
- Cut suite runtime ~38% with parallel execution (pytest-xdist) via per-worker database and server isolation; eliminated flaky failures with explicit-wait page reload handling.
- Set up a GitHub Actions pipeline with a smoke-test gate, full regression, and HTML reports with failure screenshots.
