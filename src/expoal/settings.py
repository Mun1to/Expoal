"""Ajustes persistentes de la app.

Hoy solo guardan de qué navegador tomar las cookies. Vive aparte del historial
porque son cosas distintas: el historial es un registro que crece, esto es una
preferencia única que se lee en cada arranque.

POR QUÉ COOKIES: muchos vídeos no fallan porque Expoal esté roto, sino porque
la plataforma pide una sesión iniciada (privados, con edad restringida, solo
para miembros, o los controles anti-bot de YouTube). yt-dlp sabe leer las
cookies del navegador que ya tienes abierto, así que basta con decirle cuál.
Las cookies NO se copian a ningún sitio: yt-dlp las lee del navegador en el
momento de descargar y se quedan en tu equipo, como todo lo demás.
"""
from __future__ import annotations

import json
import sys

from . import config

# Navegadores que yt-dlp sabe leer. Safari solo existe en macOS, así que no se
# ofrece fuera de ahí para no enseñar una opción que siempre fallaría.
BROWSERS: tuple[str, ...] = (
    "chrome",
    "firefox",
    "edge",
    "brave",
    "opera",
    "vivaldi",
    "chromium",
    "whale",
) + (("safari",) if sys.platform == "darwin" else ())

_DEFAULTS: dict = {"cookies_browser": ""}


def load() -> dict:
    """Lee los ajustes. Si el archivo no está o está corrupto, vuelve a los valores por defecto."""
    data = dict(_DEFAULTS)
    try:
        raw = json.loads(config.SETTINGS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return data
    if isinstance(raw, dict):
        data.update({k: v for k, v in raw.items() if k in _DEFAULTS})
    return data


def save(data: dict) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    current = load()
    current.update({k: v for k, v in data.items() if k in _DEFAULTS})
    config.SETTINGS_FILE.write_text(
        json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def cookies_browser() -> str:
    name = str(load().get("cookies_browser") or "").lower()
    return name if name in BROWSERS else ""


def set_cookies_browser(name: str) -> str:
    """Guarda el navegador elegido. Cadena vacía = no usar cookies."""
    name = str(name or "").lower()
    if name and name not in BROWSERS:
        raise ValueError(f"Navegador no soportado: {name}")
    save({"cookies_browser": name})
    return name


def cookie_opts() -> dict:
    """Fragmento de opciones para yt-dlp, vacío si no hay navegador elegido.

    La tupla de un solo elemento es la forma que espera yt-dlp
    (navegador, perfil, llavero, contenedor); los tres últimos van por defecto.
    """
    name = cookies_browser()
    return {"cookiesfrombrowser": (name,)} if name else {}


# Señales de que lo que falla es la falta de sesión, no el vídeo ni la app. La
# más fiable es la propia sugerencia de yt-dlp, que nombra la opción de cookies.
_LOGIN_HINTS = (
    "cookies-from-browser",
    "sign in to confirm your age",
    "sign in to confirm you're not a bot",
    "confirm you're not a bot",
    "this video is private",
    "private video",
    "members-only",
    "join this channel",
    "age-restricted",
    "login required",
    "requires authentication",
    "account associated with this",
)


def looks_like_login_error(message: str) -> bool:
    low = (message or "").lower()
    return any(hint in low for hint in _LOGIN_HINTS)


# Cuando las cookies SÍ están configuradas pero no se pueden leer. El caso
# gordo es Chrome en Windows: desde la versión 127 cifra las cookies de forma
# que yt-dlp no puede descifrarlas, y Firefox se convierte en la vía fiable.
_COOKIE_FAIL_HINTS = (
    "could not copy",
    "failed to decrypt",
    "unable to decrypt",
    "dpapi",
    "no such file or directory",
    "could not find",
    "permission denied",
    "browser is not installed",
    "unsupported browser",
)


def looks_like_cookie_error(message: str) -> bool:
    low = (message or "").lower()
    if not any(hint in low for hint in _COOKIE_FAIL_HINTS):
        return False
    # Solo cuenta si el fallo habla de cookies o del navegador elegido: hay
    # errores de "no such file" que no tienen nada que ver.
    return "cookie" in low or (cookies_browser() and cookies_browser() in low)
