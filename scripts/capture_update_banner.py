"""Captura el banner de actualización simulando que hay una versión nueva."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "assets" / "update-banner-check.png"
MOCK = {
    "update_available": True,
    "current": "1.0.0",
    "latest": "1.1.0",
    "notes_url": "https://github.com/Mun1to/Expoal/releases/latest",
    "installer_url": "https://github.com/Mun1to/Expoal/releases/download/v1.1.0/Expoal-1.1.0-setup.exe",
    "can_auto_install": True,
}

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1000, "height": 500}, device_scale_factor=2)
    page.route(
        "**/api/update/check*",
        lambda route: route.fulfill(
            status=200, content_type="application/json", body=json.dumps(MOCK)
        ),
    )
    page.goto("http://127.0.0.1:8710", wait_until="networkidle")
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    page.wait_for_selector("#update-banner:not(.hidden)", timeout=8000)
    page.wait_for_timeout(400)
    page.locator("main").screenshot(path=str(OUT))
    browser.close()
print("banner capturado en", OUT)
