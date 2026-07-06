"""Captura solo la cabecera (.topbar) para revisar la alineación del logotipo."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "assets" / "header-check.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 900, "height": 300}, device_scale_factor=3)
    page.goto("http://127.0.0.1:8710", wait_until="networkidle")
    page.evaluate("document.documentElement.dataset.theme = 'dark'")
    page.wait_for_timeout(300)
    page.locator(".brand").screenshot(path=str(OUT))
    browser.close()
print("cabecera capturada en", OUT)
