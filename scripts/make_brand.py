"""Genera todos los iconos de Expoal a partir del logo original.

Fuente: assets/logo.png (logo sin fondo, transparente).
Salidas: el .ico de la app/instalador/carpeta y los PNG de la interfaz y la web.

El logo es azul con contorno blanco, sin negro, así que se lee sobre cualquier
fondo: todo se genera transparente, sin lienzo detrás.

Uso: uv run python scripts/make_brand.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent.parent
SOURCE = ROOT / "assets" / "logo.png"

BRAND_BLUE = "#0069FF"
MARGIN = 0.06               # respiro mínimo en los iconos (fracción del lado)
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def square_icon(size: int, logo: Image.Image) -> Image.Image:
    """Logo centrado en un lienzo cuadrado transparente."""
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = max(1, int(size * (1 - 2 * MARGIN)))
    fitted = logo.copy()
    fitted.thumbnail((inner, inner), Image.LANCZOS)
    canvas.paste(
        fitted,
        ((size - fitted.width) // 2, (size - fitted.height) // 2),
        fitted,
    )
    return canvas


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Falta el logo original en {SOURCE}")

    logo = Image.open(SOURCE).convert("RGBA")
    logo = logo.crop(logo.getbbox())  # quita el aire transparente sobrante

    icons = {size: square_icon(size, logo) for size in ICO_SIZES}
    big = square_icon(512, logo)

    # Icono multi-resolución para el .exe, el instalador y la carpeta de Windows
    ico_path = ROOT / "assets" / "expoal.ico"
    icons[256].save(ico_path, format="ICO",
                    sizes=[(s, s) for s in ICO_SIZES],
                    append_images=[icons[s] for s in ICO_SIZES if s != 256])
    print("icono de Windows:", ico_path)

    # PNG del icono para la interfaz, la web y el README
    for path in (
        ROOT / "assets" / "icon-256.png",
        ROOT / "src" / "expoal" / "web" / "icon.png",
        ROOT / "site" / "assets" / "icon-256.png",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        big.resize((256, 256), Image.LANCZOS).save(path, optimize=True)
        print("icono PNG:", path)

    # Logo suelto (sin lienzo) para usos sobre fondo claro
    plain = logo.copy()
    plain.thumbnail((512, 512), Image.LANCZOS)
    plain.save(ROOT / "assets" / "logo-512.png", optimize=True)
    print("logo suelto:", ROOT / "assets" / "logo-512.png")

    # Logo transparente para las cabeceras de la app y de la web, donde el fondo lo
    # controlamos nosotros y el lienzo blanco sobraría.
    header = logo.copy()
    header.thumbnail((160, 160), Image.LANCZOS)
    for path in (
        ROOT / "src" / "expoal" / "web" / "logo.png",
        ROOT / "site" / "assets" / "logo.png",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        header.save(path, optimize=True)
        print("logo de cabecera:", path)
    print("azul de marca:", BRAND_BLUE)


if __name__ == "__main__":
    main()
