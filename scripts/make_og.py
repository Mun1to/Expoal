"""Genera la imagen Open Graph (1200x630) para compartir en redes.

Renderiza una tarjeta HTML con Playwright y la guarda en site/assets/og.png y
assets/og.png. Uso: uv run python scripts/make_og.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.parent
# La tarjeta va SIEMPRE en inglés, aunque la web se adapte al idioma del visitante:
# es una sola imagen para todo el mundo y se comparte sobre todo fuera de España.
SHOT = (ROOT / "assets" / "screenshot-dark-en.png").resolve().as_uri()
ICON = (ROOT / "assets" / "logo-512.png").resolve().as_uri()

HTML = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ width: 1200px; height: 630px; overflow: hidden; }}
  body {{
    font-family: "Segoe UI Variable Text", "Segoe UI", system-ui, sans-serif;
    background:
      radial-gradient(700px 500px at 78% 30%, rgba(0,105,255,0.30), transparent 60%),
      #0B0F1F;
    color: #E9EDF8; display: flex; align-items: center; height: 630px;
  }}
  .left {{ width: 560px; padding: 0 0 0 72px; flex-shrink: 0; }}
  .brand {{ display: flex; align-items: center; gap: 16px; margin-bottom: 30px; }}
  .brand img {{ width: 78px; height: 78px; object-fit: contain; }}
  .brand span {{ font-size: 40px; font-weight: 700; letter-spacing: -0.5px; }}
  h1 {{
    font-size: 62px; font-weight: 750; line-height: 1.04; letter-spacing: -1.6px;
    margin-bottom: 22px;
  }}
  h1 .grad {{ color: #3B87FF; }}
  p {{ font-size: 25px; color: #93A0C7; line-height: 1.4; margin-bottom: 30px; }}
  p b {{ color: #E9EDF8; font-weight: 600; }}
  .right {{ flex: 1; height: 630px; position: relative; overflow: hidden; }}
  .right img {{
    position: absolute; top: 82px; left: 40px; width: 760px;
    border-radius: 18px 18px 0 0; border: 1px solid #243052;
    box-shadow: 0 40px 90px rgba(0,0,0,0.6);
  }}
</style></head>
<body>
  <div class="left">
    <div class="brand"><img src="{ICON}"><span>Expoal</span></div>
    <h1>From link<br><span class="grad">to disk.</span></h1>
    <p>Download videos from YouTube, TikTok and Instagram straight to your computer.<br><b>100% open source, local and free.</b></p>
  </div>
  <div class="right"><img src="{SHOT}"></div>
</body></html>
"""


def main() -> None:
    tmp = ROOT / "scripts" / "_og_tmp.html"
    tmp.write_text(HTML, encoding="utf-8")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": 1200, "height": 630}, device_scale_factor=2
            )
            page.goto(tmp.resolve().as_uri(), wait_until="networkidle")
            page.wait_for_timeout(400)
            out_site = ROOT / "site" / "assets" / "og.png"
            page.screenshot(path=str(out_site))
            browser.close()
        (ROOT / "assets" / "og.png").write_bytes(out_site.read_bytes())
        print("OG generada:", out_site)
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
