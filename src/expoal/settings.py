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
from pathlib import Path

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

# Casillas para lo que casi todo el mundo quiere y nadie debería tener que
# escribir a mano. Cada una es LITERALMENTE la opción de yt-dlp que le
# corresponde: así no hay una segunda implementación que mantener, se traducen
# por el mismo camino que las opciones avanzadas y no pueden desincronizarse.
TOGGLES: dict[str, str] = {
    "sponsorblock": "--sponsorblock-remove sponsor",
    "embed_thumbnail": "--embed-thumbnail",
    "embed_metadata": "--embed-metadata",
    "embed_chapters": "--embed-chapters",
    "embed_subs": "--embed-subs",
    # Velocidad. YouTube y compañía sirven el vídeo troceado en fragmentos, y
    # bajarlos de uno en uno desaprovecha la conexión. Esto es de yt-dlp, no
    # necesita nada instalado, y es la mejora de velocidad más barata que hay.
    "fast_fragments": "--concurrent-fragments 4",
    # La ruta real la pone toggle_flags(): aria2c puede estar en el PATH o
    # sencillamente al lado del .exe, y hay que decirle a yt-dlp cuál usar.
    "aria2c": '--downloader aria2c --downloader-args "aria2c:-x 16 -s 16 -k 1M"',
}

# Las que recortan o reescriben el archivo necesitan FFmpeg sí o sí.
TOGGLES_NEED_FFMPEG: frozenset[str] = frozenset(
    {"sponsorblock", "embed_thumbnail", "embed_chapters", "embed_subs"}
)

# Y esta necesita un programa que Expoal no trae ni instala por su cuenta.
TOGGLES_NEED_ARIA2C: frozenset[str] = frozenset({"aria2c"})

# Las que solo tocan la VELOCIDAD y dejan el archivo igual. La distinción
# importa para el recorte en origen (clipper.py): ese camino se salta los
# postprocesadores de yt-dlp, así que solo vale cuando nadie ha pedido nada que
# reescriba el archivo. Que alguien tenga marcada la descarga rápida no puede
# costarle el atajo.
TOGGLES_SPEED_ONLY: frozenset[str] = frozenset({"fast_fragments", "aria2c"})

_DEFAULTS: dict = {
    "cookies_browser": "",
    "cookies_file": "",
    "extra_args": "",
    **{name: False for name in TOGGLES},
    # Los fragmentos en paralelo vienen puestos: es de yt-dlp, no necesita nada
    # instalado, no cambia el archivo que sale y donde no aplica no estorba. Una
    # mejora gratis no debería estar detrás de una casilla que nadie encuentra.
    "fast_fragments": True,
    # Marca de que ya se aplicaron los valores nuevos a un archivo viejo. Sin
    # esto, quien ya tenía Expoal se quedaría para siempre con los de antes,
    # porque su archivo guarda todas las casillas en false aunque no las haya
    # tocado nunca. Ver upgrade_defaults().
    "defaults_v2": False,
}


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


def upgrade_defaults() -> None:
    """Estrena los valores nuevos en una instalación que ya existía.

    Solo toca las casillas de VELOCIDAD, que no cambian el archivo que sale y
    por tanto no pueden estropearle el resultado a nadie. Se hace una sola vez;
    si luego el usuario la desmarca, se queda desmarcada.
    """
    data = load()
    if data.get("defaults_v2"):
        return
    save({"fast_fragments": True, "defaults_v2": True})


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
    """Guarda el navegador elegido. Cadena vacía = no usar cookies.

    Elegir navegador borra el archivo de cookies y al revés: son dos formas de
    lo mismo, y tener las dos puestas dejaría al usuario sin saber cuál manda.
    """
    name = str(name or "").lower()
    if name and name not in BROWSERS:
        raise ValueError(f"Navegador no soportado: {name}")
    save({"cookies_browser": name, "cookies_file": ""})
    return name


def cookies_file() -> str:
    return str(load().get("cookies_file") or "")


def set_cookies_file(path: str) -> str:
    """Guarda un archivo cookies.txt exportado del navegador.

    POR QUÉ existe además de leer el navegador: Chrome y Edge en Windows cifran
    sus cookies desde la versión 127 de una forma que yt-dlp no puede descifrar,
    así que a quien use esos navegadores no le queda otra salida. Con una
    extensión de las de "exportar cookies" saca un archivo y lo elige aquí.
    """
    path = str(path or "").strip()
    if path:
        if not Path(path).is_file():
            raise ValueError("Ese archivo de cookies no existe")
        save({"cookies_file": path, "cookies_browser": ""})
    else:
        save({"cookies_file": ""})
    return path


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


def toggles() -> dict[str, bool]:
    data = load()
    return {name: bool(data.get(name)) for name in TOGGLES}


def set_toggle(name: str, value: bool) -> bool:
    if name not in TOGGLES:
        raise ValueError(f"Opción desconocida: {name}")
    save({name: bool(value)})
    return bool(value)


def toggle_flags(name: str) -> str:
    """La cadena de flags de una casilla, resuelta para este equipo.

    Todas son literales salvo aria2c: hay que decirle a yt-dlp DÓNDE está el
    programa, porque puede estar en el PATH o simplemente al lado del .exe. Si
    no aparece por ningún lado, la casilla no aporta flags: mejor bajar a
    velocidad normal que reventar la descarga por un binario que ya no está.
    """
    if name == "aria2c":
        path = config.find_aria2c()
        if not path:
            return ""
        return f'--downloader {shlex.quote(path)} --downloader-args "aria2c:-x 16 -s 16 -k 1M"'
    if name in TOGGLES_NEED_FFMPEG and not config.ffmpeg_available():
        return ""
    return TOGGLES.get(name, "")


def user_args_line() -> str:
    """Todo lo que ha pedido el usuario, casillas y texto libre, en una sola línea.

    Se juntan a propósito antes de traducir, para que sea el propio yt-dlp quien
    resuelva la combinación (sumar postprocesadores, resolver repetidos). Si se
    tradujeran por separado habría que reimplementar esa lógica a mano.
    El texto libre va al final: quien escribe flags manda sobre las casillas.
    """
    marked_names = toggles()   # una sola lectura del archivo, no una por casilla
    parts = [flags for name in TOGGLES if marked_names.get(name) and (flags := toggle_flags(name))]
    free = extra_args()
    if free:
        parts.append(free)
    return " ".join(parts)


def rewrites_the_file() -> bool:
    """¿Ha pedido el usuario algo que reescriba el archivo ya descargado?

    Lo mira el recorte en origen antes de coger su atajo: ese camino descarga
    los bytes a mano y no pasa por los postprocesadores de yt-dlp, así que con
    cualquiera de estas puestas hay que ir por el camino de siempre.
    """
    marked = toggles()
    if any(marked.get(name) for name in TOGGLES if name not in TOGGLES_SPEED_ONLY):
        return True
    return bool(extra_args())


def user_opts() -> dict:
    """Lo que pidió el usuario, ya traducido; vacío si dejó de valer."""
    try:
        return parse_extra_args(user_args_line())
    except ArgsError:
        # Guardadas válidas pero rotas por un cambio de yt-dlp: mejor descargar
        # sin ellas que no descargar.
        return {}


def cookie_opts() -> dict:
    """Fragmento de opciones para yt-dlp, vacío si no hay cookies configuradas.

    La tupla de un solo elemento es la forma que espera yt-dlp
    (navegador, perfil, llavero, contenedor); los tres últimos van por defecto.
    El archivo es la alternativa para quien no puede leer las del navegador.
    """
    name = cookies_browser()
    if name:
        return {"cookiesfrombrowser": (name,)}
    path = cookies_file()
    # Si el archivo desapareció, mejor bajar sin cookies que fallar con un error
    # sobre un archivo que el usuario eligió hace semanas y ya no recuerda.
    if path and Path(path).is_file():
        return {"cookiefile": path}
    return {}


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
