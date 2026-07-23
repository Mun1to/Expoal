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

import contextlib
import io
import json
import re
import shlex
import sys

import yt_dlp

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

_DEFAULTS: dict = {"cookies_browser": "", "extra_args": ""}


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


# Opciones de yt-dlp que NO se aceptan aunque las escriba el usuario. No es
# desconfiar de él: es que estas ejecutan programas arbitrarios, y basta con que
# alguien en un foro le diga "pega esto para arreglar tal cosa" para convertir
# un descargador en la puerta de entrada de cualquier comando. Quien de verdad
# necesite esto tiene el yt-dlp de línea de comandos.
BLOCKED_ARGS: tuple[str, ...] = (
    "--exec",
    "--exec-before-download",
    "--config-location",
    "--config-locations",
)


class ArgsError(ValueError):
    """El texto de opciones avanzadas no se puede usar; el mensaje explica por qué."""


def parse_extra_args(text: str) -> dict:
    """Convierte flags de yt-dlp ("--embed-thumbnail") en opciones de la librería.

    Expoal usa yt-dlp como librería, no como comando, así que hay que traducir.
    `yt_dlp.parse_options` hace justo eso, con la MISMA sintaxis que la
    documentación oficial, que es lo que el usuario va a copiar de internet.

    GOTCHA: parse_options devuelve el diccionario COMPLETO, con los cien y pico
    valores por defecto de yt-dlp. Aplicarlo entero pisaría el formato, la
    plantilla de salida y media configuración de la app, así que se compara
    contra un parseo vacío y solo se queda lo que el usuario cambió de verdad.
    """
    text = (text or "").strip()
    if not text:
        return {}

    try:
        argv = shlex.split(text)
    except ValueError as exc:
        raise ArgsError(f"Comillas sin cerrar: {exc}") from exc

    for arg in argv:
        name = arg.split("=", 1)[0].lower()
        if name in BLOCKED_ARGS:
            raise ArgsError(
                f"{name} no se permite desde aquí porque ejecuta programas en tu equipo"
            )

    # optparse escribe en la salida antes de rendirse: con --help suelta el
    # manual entero de yt-dlp, y en el .exe sin consola no lo lee nadie. Se
    # desvía a un buffer para que solo salga el mensaje que le damos al usuario.
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            parsed = yt_dlp.parse_options(argv)
    except SystemExit as exc:
        # optparse llama a sys.exit con --help o --version.
        raise ArgsError("Esas opciones no descargan nada, solo muestran información") from exc
    except Exception as exc:
        # optparse antepone el nombre del programa ("expoal: error: ..."), que
        # aquí no dice nada: el usuario ya sabe en qué app está escribiendo.
        message = str(exc).strip().splitlines()[-1] if str(exc).strip() else str(exc)
        message = re.sub(r"^\S*:\s*error:\s*", "", message.strip())
        raise ArgsError(message or "Opciones no válidas") from exc

    if parsed.urls:
        raise ArgsError("Escribe solo opciones, no enlaces")

    baseline = _baseline_opts()
    return {k: v for k, v in parsed.ydl_opts.items() if k not in baseline or baseline[k] != v}


_BASELINE: dict | None = None


def _baseline_opts() -> dict:
    """Las opciones que produce un parseo vacío, para saber qué cambió el usuario."""
    global _BASELINE
    if _BASELINE is None:
        _BASELINE = dict(yt_dlp.parse_options([]).ydl_opts)
    return _BASELINE


def extra_args() -> str:
    return str(load().get("extra_args") or "")


def set_extra_args(text: str) -> str:
    """Guarda las opciones avanzadas. Valida antes: guardar algo roto no ayuda a nadie."""
    text = (text or "").strip()
    parse_extra_args(text)  # levanta ArgsError si no valen
    save({"extra_args": text})
    return text


def extra_opts() -> dict:
    """Opciones avanzadas ya traducidas, o vacío si no hay o si dejaron de valer."""
    try:
        return parse_extra_args(extra_args())
    except ArgsError:
        # Guardadas válidas pero rotas por un cambio de yt-dlp: mejor descargar
        # sin ellas que no descargar.
        return {}


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
