"""Captura la landing (site/index.html) para verificarla visualmente."""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.parent
LANDING = (ROOT / "site" / "index.html").resolve().as_uri()
OUT = ROOT / "assets" / "landing-preview.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1100, "height": 900}, device_scale_factor=1)
    page.goto(LANDING, wait_until="networkidle")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT), full_page=True)
    browser.close()
print("landing capturada en", OUT)
