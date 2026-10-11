"""
Pytest fixtures for the ShopLite UI + database test suite.

- app_server : starts the store once per test session on a local port
- db         : resets the database to seed data before EVERY test (isolation)
- driver     : a fresh Chrome per test (clean cookies/cart), headless by default
- logged_in  : a driver already signed in as a standard customer
- On failure, a screenshot is saved to reports/screenshots and embedded in the HTML report.
"""
import os
import threading
from datetime import datetime
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from werkzeug.serving import make_server

from app.store import create_app, init_db
from pages.login_page import LoginPage
from pages.products_page import ProductsPage
from utils.db import DbClient

ROOT = Path(__file__).resolve().parent
# Each pytest-xdist worker (gw0, gw1, ...) gets its own app port and database,
# so the suite can run in parallel with `pytest -n 4` without tests colliding.
WORKER = int(os.getenv("PYTEST_XDIST_WORKER", "gw0")[2:])
DB_PATH = str(ROOT / "reports" / f"test_shoplite_{WORKER}.db")
SCREENSHOTS = ROOT / "reports" / "screenshots"
PORT = int(os.getenv("APP_PORT", "5055")) + WORKER
BASE_URL = f"http://127.0.0.1:{PORT}"

STANDARD_USER = {"email": "alice@shoplite.test", "password": "Passw0rd!", "name": "Alice Johnson"}


def pytest_addoption(parser):
    parser.addoption("--headed", action="store_true", help="Show the browser window")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session", autouse=True)
def app_server():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)
    server = make_server("127.0.0.1", PORT, create_app(DB_PATH), threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield
    server.shutdown()


@pytest.fixture
def db():
    init_db(DB_PATH)  # fresh seed data for every test
    return DbClient(DB_PATH)


@pytest.fixture
def driver(request, db):
    opts = webdriver.ChromeOptions()
    if not request.config.getoption("--headed"):
        opts.add_argument("--headless=new")
    for arg in ("--no-sandbox", "--disable-dev-shm-usage", "--window-size=1366,900",
                "--disable-background-networking",
                "--disable-features=PasswordLeakDetection,AutofillServerCommunication"):
        opts.add_argument(arg)
    # Stop Chrome's password-manager popups from stealing focus mid-test
    opts.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False,
    })
    if os.getenv("CHROME_BINARY"):
        opts.binary_location = os.environ["CHROME_BINARY"]
    # Selenium Manager finds a matching driver automatically; CHROMEDRIVER_PATH overrides it.
    service = Service(os.environ["CHROMEDRIVER_PATH"]) if os.getenv("CHROMEDRIVER_PATH") else Service()
    drv = webdriver.Chrome(options=opts, service=service)
    drv.implicitly_wait(0)  # explicit waits only - avoids flaky mixed waits
    yield drv
    drv.quit()


@pytest.fixture
def logged_in(driver, base_url):
    LoginPage(driver, base_url).open().login(STANDARD_USER["email"], STANDARD_USER["password"])
    page = ProductsPage(driver, base_url)
    page.find(page.CARD)  # wait until catalogue renders
    return page


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed and "driver" in item.fixturenames:
        drv = item.funcargs["driver"]
        SCREENSHOTS.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOTS / f"{item.name}_{datetime.now():%H%M%S}.png"
        drv.save_screenshot(str(path))
        html = item.config.pluginmanager.getplugin("html")
        if html:
            extras = getattr(report, "extras", [])
            extras.append(html.extras.png(drv.get_screenshot_as_base64()))
            report.extras = extras
