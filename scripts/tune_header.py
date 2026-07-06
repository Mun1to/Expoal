"""Compara varios desplazamientos verticales del tagline para centrarlo con el logo.

Renderiza filas con distintos `top` y una línea guía en el centro de las mayúsculas
de "Expoal" (medido con canvas), para elegir el valor exacto. Salida temporal.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent.parent / "assets" / "header-tune.png"
OFFSETS = [-3, -2, -1, 0, 1]

rows = "\n".join(
    f"""<div class="row">
      <div class="brand">
        <div class="icon">&#9660;</div>
        <h1>Expoal</h1>
        <span class="tagline" style="top:{o}px">DEL LINK A TU DISCO</span>
      </div>
      <span class="lbl">top: {o}px</span>
    </div>"""
    for o in OFFSETS
)

HTML = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0B0F1F; font-family:"Segoe UI Variable Text","Segoe UI",sans-serif;
          padding:26px 40px; }}
  .row {{ display:flex; align-items:center; gap:24px; height:64px;
          border-bottom:1px solid #1a2340; position:relative; }}
  .brand {{ display:flex; align-items:center; gap:12px; position:relative; }}
  .icon {{ width:30px; height:30px; border-radius:8px; background:#182242;
           color:#E8B84B; display:grid; place-items:center; font-size:15px; }}
  h1 {{ color:#E9EDF8; font-size:22px; font-weight:650; letter-spacing:-0.4px;
        line-height:1; position:relative; }}
  /* guia: centro vertical de las mayusculas de Expoal (~cap height / 2 desde el top del glifo) */
  h1::after {{ content:""; position:absolute; left:0; right:0; top:50%;
    border-top:1px dashed rgba(232,184,75,0.6); }}
  .tagline {{ color:#93A0C7; font-size:12px; text-transform:uppercase;
    letter-spacing:0.09em; margin-left:4px; line-height:1; position:relative; }}
  .lbl {{ color:#556; font-size:12px; font-family:monospace; margin-left:auto; }}
</style></head><body>{rows}</body></html>"""


def main() -> None:
    tmp = Path(__file__).parent / "_tune_tmp.html"
    tmp.write_text(HTML, encoding="utf-8")
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page(viewport={"width": 620, "height": 360}, device_scale_factor=3)
            page.goto(tmp.resolve().as_uri())
            page.wait_for_timeout(200)
            page.screenshot(path=str(OUT))
            b.close()
        print("comparativa en", OUT)
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
