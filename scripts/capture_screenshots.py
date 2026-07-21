"""Genera las capturas de la interfaz (tema claro/oscuro x idioma es/en) con Playwright.

Requiere el servidor web de Expoal corriendo (por defecto en 127.0.0.1:8710).
Uso: uv run python scripts/capture_screenshots.py

El historial de ejemplo se INYECTA interceptando /api/history, así que el script
no toca el historial real de quien lo ejecuta y sale siempre igual en cualquier
máquina. La carpeta de destino se reescribe a una ruta genérica por lo mismo:
las capturas se publican y no deben enseñar el nombre de usuario de nadie.
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8710"
VIDEO = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
FOLDER = r"C:\Users\You\Downloads\Expoal"
OUT = Path(__file__).parent.parent / "assets"

SHOW_JOBS = False

# La cola en marcha: un vídeo bajando (con barra, velocidad y botón de cancelar)
# y otro terminado (con el botón de abrir carpeta). Se inyecta igual que el
# historial en vez de descargar de verdad: así la captura sale idéntica siempre
# y no deja archivos en el disco de quien la genera.
JOBS = [
    {
        "id": "capture-1",
        "url": "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
        "mode": "video",
        "quality": "1080",
        "title": "Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film",
        "status": "descargando",
        "progress": 34.6,
        "speed": "7.3 MB/s",
        "eta": "49s",
        "error": None,
        "file_path": None,
    },
    {
        "id": "capture-2",
        "url": "https://www.youtube.com/watch?v=YE7VzlLtp-4",
        "mode": "video",
        "quality": "1080",
        "title": "Tears of Steel - Blender Foundation open movie",
        "status": "completado",
        "progress": 100,
        "speed": None,
        "eta": None,
        "error": None,
        "file_path": rf"{FOLDER}\Tears of Steel [YE7VzlLtp-4].mp4",
    },
]

HISTORY = [
    {
        "url": "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
        "title": "Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film",
        "platform": "Youtube",
        "mode": "video",
        "quality": "1080",
        "file_path": rf"{FOLDER}\Big Buck Bunny 60fps 4K [aqz-KE-bpKQ].mp4",
        "downloaded_at": "2026-07-21T20:14:22",
    },
    {
        "url": "https://www.youtube.com/watch?v=8S0FDjFBj8o",
        "title": "How to sound smart in your TEDx Talk | Will Stephen",
        "platform": "Youtube",
        "mode": "text",
        "quality": "best",
        "file_path": rf"{FOLDER}\How to sound smart in your TEDx Talk [8S0FDjFBj8o].en.txt",
        "downloaded_at": "2026-07-21T20:11:05",
    },
    {
        "url": "https://www.youtube.com/watch?v=YE7VzlLtp-4",
        "title": "Tears of Steel - Blender Foundation open movie",
        "platform": "Youtube",
        "mode": "audio",
        "quality": "best",
        "file_path": rf"{FOLDER}\Tears of Steel [YE7VzlLtp-4].mp3",
        "downloaded_at": "2026-07-21T20:08:47",
    },
]


def fake_history(route, request):
    # Solo el GET: el DELETE de "Vaciar" no se toca.
    if request.method != "GET":
        route.continue_()
        return
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(HISTORY),
    )


def fake_jobs(route, request):
    if request.method != "GET":
        route.continue_()
        return
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(JOBS if SHOW_JOBS else []),
    )


def capture(page, theme: str, lang: str) -> None:
    page.goto(URL, wait_until="networkidle")
    page.evaluate(
        "([t, l]) => { localStorage.setItem('expoal-theme', t);"
        " localStorage.setItem('expoal-lang', l); }",
        [theme, lang],
    )
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
    page.fill("#folder-input", FOLDER)
    # Sin esto el campo recién rellenado sale con el anillo de foco encendido
    page.evaluate("() => document.activeElement && document.activeElement.blur()")
    page.wait_for_timeout(700)
    filename = f"screenshot-{theme}-{lang}.png"
    # Sin full_page a propósito: la página entera sale como una tira vertical que
    # se lee como captura de web. Al alto de la ventana se lee como app, y aun
    # así entra todo lo que importa (enlace, vídeo, opciones e historial).
    page.screenshot(path=str(OUT / filename))
    print("guardada:", filename)


def capture_queue(page, theme: str, lang: str) -> None:
    """La cola trabajando: es lo que prueba que la app HACE algo, no solo que existe."""
    page.goto(URL, wait_until="networkidle")
    page.evaluate(
        "([t, l]) => { localStorage.setItem('expoal-theme', t);"
        " localStorage.setItem('expoal-lang', l); }",
        [theme, lang],
    )
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#queue-section:not(.hidden)", timeout=10000)
    page.wait_for_selector("#history-section:not(.hidden)", timeout=10000)
    page.wait_for_timeout(700)
    filename = f"screenshot-queue-{theme}-{lang}.png"
    page.screenshot(path=str(OUT / filename))
    print("guardada:", filename)


def main() -> None:
    global SHOW_JOBS
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1080, "height": 810}, device_scale_factor=2
        )
        page.route("**/api/history", fake_history)
        page.route("**/api/jobs", fake_jobs)
        for theme in ("dark", "light"):
            for lang in ("es", "en"):
                capture(page, theme, lang)
        SHOW_JOBS = True
        for theme in ("dark", "light"):
            for lang in ("es", "en"):
                capture_queue(page, theme, lang)
        browser.close()
    print("Capturas listas en", OUT)


if __name__ == "__main__":
    main()
