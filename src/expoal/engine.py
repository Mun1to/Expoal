"""Motor actualizable: renueva yt-dlp sin reinstalar Expoal.

yt-dlp viaja empaquetado dentro de la app, pero YouTube cambia cada pocas
semanas y un motor viejo se ve como "Expoal no funciona" aunque la app esté
perfecta. Este módulo baja el wheel oficial de PyPI, lo deja en el directorio
de datos del usuario y hace que Python cargue esa copia en vez de la
empaquetada. Así el motor se renueva con un clic entre versiones de la app.

Seguridad: solo se consulta pypi.org y solo se descarga de
files.pythonhosted.org (los dominios oficiales de PyPI), siempre por HTTPS y
verificando el sha256 que publica el propio PyPI. El zip se extrae filtrando
rutas: nada fuera de yt_dlp/ y nada con ".." (anti zip-slip).

GOTCHA CRÍTICO (PyInstaller): el .exe congelado resuelve los imports con su
propio finder, que puede ganar a sys.path; añadir la carpeta del motor a
sys.path no es fiable dentro del .exe. Por eso activate() inserta un finder
propio al PRINCIPIO de sys.meta_path (el primer eslabón de la cadena de
import, gana a todo) y reclama también los submódulos yt_dlp.* para que nunca
se mezclen un paquete nuevo con submódulos viejos empaquetados. activate()
debe llamarse antes del primer `import yt_dlp`: hoy es la primera línea de
main() en __main__.py.
"""
from __future__ import annotations

import hashlib
import importlib.machinery
import json
import shutil
import sys
import threading
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from . import __version__, config

ENGINE_DIR = config.DATA_DIR / "engine"
META_FILE = ENGINE_DIR / "engine.json"
PYPI_JSON = "https://pypi.org/pypi/yt-dlp/json"
DOWNLOAD_HOST = "files.pythonhosted.org"
USER_AGENT = f"Expoal/{__version__}"

_lock = threading.Lock()
_cache: dict | None = None


class _EngineFinder:
    """Redirige todos los imports de yt_dlp a la copia descargada del motor."""

    def find_spec(self, fullname: str, path=None, target=None):
        if fullname != "yt_dlp" and not fullname.startswith("yt_dlp."):
            return None
        if fullname == "yt_dlp":
            search = [str(ENGINE_DIR)]
        else:
            # Submódulo: se busca su hoja dentro de la carpeta del paquete padre
            # (PathFinder busca el último tramo del nombre en las rutas dadas).
            parent = ENGINE_DIR.joinpath(*fullname.split(".")[:-1])
            search = [str(parent)]
        return importlib.machinery.PathFinder.find_spec(fullname, search)


def _discard() -> None:
    shutil.rmtree(ENGINE_DIR, ignore_errors=True)


def activate() -> str | None:
    """Engancha el motor descargado si existe y pertenece a esta versión de la app.

    Si la app se actualizó desde que se descargó el motor, la copia se borra:
    la app nueva trae su propio yt-dlp reciente y así no hay que comparar
    versiones entre el empaquetado (ilegible sin importarlo) y el descargado.
    """
    try:
        if not (ENGINE_DIR / "yt_dlp" / "__init__.py").exists():
            return None
        meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _discard()
        return None
    if meta.get("app") != __version__:
        _discard()
        return None
    sys.meta_path.insert(0, _EngineFinder())
    return str(meta.get("yt_dlp") or "")


def current_version() -> str:
    import yt_dlp  # tras activate(): refleja el motor realmente en uso

    return yt_dlp.version.__version__


def _as_tuple(version: str) -> tuple[int, ...]:
    # yt-dlp escribe "2026.07.04" y PyPI lo normaliza a "2026.7.4": comparar
    # como números iguala ambos formatos.
    parts = []
    for chunk in version.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check(force: bool = False) -> dict:
    """Consulta PyPI y dice si hay un motor más nuevo que el que corre ahora."""
    global _cache
    with _lock:
        if _cache is not None and not force:
            return _cache
    result: dict = {"current": current_version(), "update_available": False}
    try:
        req = urllib.request.Request(PYPI_JSON, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        latest = data["info"]["version"]
        wheel = next(
            f for f in data["releases"][latest]
            if f.get("filename", "").endswith("py3-none-any.whl")
        )
    except Exception:  # noqa: BLE001 - sin conexión no es un error visible
        result["error"] = "no se pudo comprobar"
        with _lock:
            _cache = result
        return result
    result.update(
        {
            "latest": latest,
            "update_available": _as_tuple(latest) > _as_tuple(result["current"]),
            "wheel_url": wheel["url"],
            "sha256": wheel["digests"]["sha256"],
        }
    )
    with _lock:
        _cache = result
    return result


def apply() -> dict:
    """Descarga, verifica e instala el motor nuevo. Pide reiniciar para usarlo.

    El reinicio es necesario porque yt_dlp ya está importado en este proceso;
    la copia nueva se engancha en el próximo arranque vía activate().
    """
    global _cache
    info = check(force=True)
    if not info.get("update_available"):
        return {"ok": False, "error": "el motor ya está al día"}
    url = info["wheel_url"]
    if (urlparse(url).hostname or "").lower() != DOWNLOAD_HOST:
        return {"ok": False, "error": "origen de descarga no permitido"}

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    wheel_tmp = config.DATA_DIR / "engine.whl.part"
    staging = config.DATA_DIR / "engine.new"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as resp, open(wheel_tmp, "wb") as fh:
            while chunk := resp.read(1 << 16):
                fh.write(chunk)
        if hashlib.sha256(wheel_tmp.read_bytes()).hexdigest() != info["sha256"]:
            return {"ok": False, "error": "el checksum del motor no coincide; descarga abortada"}

        shutil.rmtree(staging, ignore_errors=True)
        with zipfile.ZipFile(wheel_tmp) as zf:
            for member in zf.namelist():
                if not member.startswith("yt_dlp/") or ".." in member:
                    continue
                zf.extract(member, staging)
        if not (staging / "yt_dlp" / "__init__.py").exists():
            return {"ok": False, "error": "el paquete descargado no contiene yt_dlp"}
        (staging / "engine.json").write_text(
            json.dumps({"yt_dlp": info["latest"], "app": __version__}),
            encoding="utf-8",
        )
        # Cambio en dos pasos: primero fuera la copia vieja, luego un rename
        # (rápido y dentro del mismo disco) de la nueva a su sitio.
        shutil.rmtree(ENGINE_DIR, ignore_errors=True)
        staging.replace(ENGINE_DIR)
    except Exception as exc:  # noqa: BLE001 - el fallo se muestra en la UI
        return {"ok": False, "error": f"fallo al actualizar el motor: {exc}"}
    finally:
        wheel_tmp.unlink(missing_ok=True)
        shutil.rmtree(staging, ignore_errors=True)

    with _lock:
        _cache = None
    return {"ok": True, "version": info["latest"], "restart_required": True}
