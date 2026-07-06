"""Genera capturas de la interfaz (tema claro y oscuro) con Playwright.

Requiere el servidor web de Expoal corriendo (por defecto en 127.0.0.1:8710) con
el historial de ejemplo ya cargado. Uso: uv run python scripts/capture_screenshots.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8710"
VIDEO = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
OUT = Path(__file__).parent.parent / "assets"


def capture(page, theme: str, filename: str) -> None:
    page.goto(URL, wait_until="networkidle")
    page.evaluate("t => localStorage.setItem('expoal-theme', t)", theme)
    page.reload(wait_until="networkidle")
    page.fill("#url-input", VIDEO)
    page.click("#analyze-btn")
    page.wait_for_selector("#preview:not(.hidden)", timeout=40000)
    page.wait_for_function(
        "() => { const t = document.querySelector('#preview-thumb');"
        " return t && t.complete && t.naturalWidth > 0; }",
        timeout=20000,
    )
    page.select_option("#quality-select", "1080")
    page.wait_for_timeout(700)
    page.screenshot(path=str(OUT / filename), full_page=True)
    print("guardada:", filename)


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1000, "height": 900}, device_scale_factor=2
        )
        capture(page, "dark", "screenshot-dark.png")
        capture(page, "light", "screenshot-light.png")
        browser.close()
    print("Capturas listas en", OUT)


if __name__ == "__main__":
    main()
