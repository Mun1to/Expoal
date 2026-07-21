"""Comprobación y aplicación de actualizaciones desde GitHub Releases.

Seguridad: solo se consulta y descarga del repositorio oficial por HTTPS. La URL
de descarga debe pertenecer a github.com/<REPO> (o a su CDN de releases). Si el
release publica `SHA256SUMS.txt`, se verifica el hash del instalador antes de
ejecutarlo. La app nunca descarga ni ejecuta nada de fuentes externas.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import urllib.request
from pathlib import Path

from . import __version__

REPO = "Mun1to/Expoal"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
# Cada plataforma se actualiza con su propio asset.
INSTALLER_SUFFIX = "-setup.exe"      # Windows: instalador Inno Setup
APPIMAGE_SUFFIX = ".AppImage"        # Linux: se reemplaza el propio AppImage
CHECKSUMS_ASSET = "SHA256SUMS.txt"
USER_AGENT = f"Expoal/{__version__}"
# La descarga solo se acepta desde estos orígenes de GitHub.
ALLOWED_HOSTS = ("github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com")

_lock = threading.Lock()
_cache: dict | None = None


def _parse_version(text: str) -> tuple[int, int, int]:
    text = text.lstrip("vV").strip()
    parts: list[int] = []
    for chunk in text.split(".")[:3]:
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return parts[0], parts[1], parts[2]


def _request(url: str, accept: str | None = None) -> urllib.request.Request:
    headers = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept
    return urllib.request.Request(url, headers=headers)


def _host_allowed(url: str) -> bool:
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower()
    return host in ALLOWED_HOSTS or host.endswith(".githubusercontent.com")


def running_appimage() -> Path | None:
    """Ruta del AppImage en ejecución, o None si no estamos dentro de uno.

    AppImage exporta la variable APPIMAGE con la ruta del archivo original.
    """
    if sys.platform != "linux":
        return None
    path = os.environ.get("APPIMAGE")
    if not path:
        return None
    p = Path(path)
    return p if p.exists() else None


def check_for_update(force: bool = False) -> dict:
    global _cache
    with _lock:
        if _cache is not None and not force:
            return _cache
    result: dict = {"update_available": False, "current": __version__}
    try:
        req = _request(API_LATEST, accept="application/vnd.github+json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001 - sin conexión no es un error visible
        result["error"] = "no se pudo comprobar"
        with _lock:
            _cache = result
        return result

    latest_tag = data.get("tag_name", "")
    version = latest_tag.lstrip("vV")
    installer_url = None
    appimage_url = None
    checksums_url = None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        url = asset.get("browser_download_url")
        # El release publica cada binario dos veces: con la versión en el nombre y con
        # un alias fijo (para los enlaces de descarga permanentes de la web). Nos
        # quedamos con el versionado, que es el canónico.
        if name.endswith(INSTALLER_SUFFIX):
            if installer_url is None or version in name:
                installer_url = url
        elif name.endswith(APPIMAGE_SUFFIX):
            if appimage_url is None or version in name:
                appimage_url = url
        elif name == CHECKSUMS_ASSET:
            checksums_url = url

    # El asset que toca según la plataforma: instalador en Windows, AppImage en Linux.
    frozen = bool(getattr(sys, "frozen", False))
    if sys.platform == "win32":
        asset_url = installer_url
        can_auto = bool(asset_url) and frozen
    else:
        asset_url = appimage_url
        can_auto = bool(asset_url) and running_appimage() is not None

    result.update(
        {
            "update_available": _parse_version(latest_tag) > _parse_version(__version__),
            "latest": latest_tag.lstrip("vV"),
            "notes_url": data.get("html_url"),
            "installer_url": asset_url,
            "checksums_url": checksums_url,
            "can_auto_install": can_auto,
        }
    )
    with _lock:
        _cache = result
    return result


def _download(url: str, dst: Path) -> None:
    if not _host_allowed(url):
        raise ValueError(f"origen de descarga no permitido: {url}")
    with urllib.request.urlopen(_request(url), timeout=60) as resp, open(dst, "wb") as fh:
        while chunk := resp.read(65536):
            fh.write(chunk)


def _expected_sha256(checksums_url: str, filename: str) -> str | None:
    try:
        with urllib.request.urlopen(_request(checksums_url), timeout=20) as resp:
            for line in resp.read().decode("utf-8").splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[1].lstrip("*") == filename:
                    return parts[0].lower()
    except Exception:  # noqa: BLE001
        return None
    return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def _quit_soon(delay: float = 1.2) -> None:
    """Cierra la app en segundo plano para que el instalador pueda reemplazarla."""

    def _quit() -> None:
        import time

        time.sleep(delay)
        os._exit(0)

    threading.Thread(target=_quit, daemon=True).start()


def _update_windows(dst: Path) -> dict:
    """Lanza el instalador en silencioso; él cierra la app, instala y la reabre."""
    try:
        subprocess.Popen(
            [str(dst), "/SILENT", "/NORESTART", "/SUPPRESSMSGBOXES"],
            close_fds=True,
        )
    except OSError as exc:
        return {"ok": False, "error": f"no se pudo iniciar el instalador: {exc}"}
    _quit_soon()
    return {"ok": True}


def _update_appimage(new_file: Path, current: Path) -> dict:
    """Sustituye el AppImage en marcha por el nuevo y relanza la app.

    En Linux se puede reemplazar el archivo de un ejecutable en uso: el proceso
    actual sigue con el inodo antiguo hasta que termina. El rename es atómico solo
    dentro del mismo sistema de archivos, así que el descargado ya viene al lado.
    """
    try:
        new_file.chmod(new_file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        os.replace(new_file, current)
    except OSError as exc:
        new_file.unlink(missing_ok=True)
        return {"ok": False, "error": f"no se pudo reemplazar el AppImage: {exc}"}

    try:
        subprocess.Popen([str(current)], close_fds=True, start_new_session=True)
    except OSError as exc:
        return {"ok": False, "error": f"actualizado, pero no se pudo relanzar: {exc}"}
    _quit_soon()
    return {"ok": True}


def apply_update() -> dict:
    info = check_for_update()
    url = info.get("installer_url")
    if not url or not info.get("can_auto_install"):
        return {"ok": False, "error": "actualización automática no disponible"}
    if not _host_allowed(url):
        return {"ok": False, "error": "origen de descarga no confiable"}

    asset_name = url.rsplit("/", 1)[-1]
    appimage = running_appimage()
    # En Linux se descarga junto al AppImage para que el reemplazo sea atómico.
    dst = (
        appimage.with_name(f".{asset_name}.new")
        if appimage
        else Path(tempfile.gettempdir()) / asset_name
    )
    try:
        _download(url, dst)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"fallo al descargar: {exc}"}

    # Verifica el checksum si el release lo publica.
    if info.get("checksums_url"):
        expected = _expected_sha256(info["checksums_url"], asset_name)
        if expected and _sha256(dst) != expected:
            dst.unlink(missing_ok=True)
            return {"ok": False, "error": "el checksum no coincide; descarga abortada"}

    if appimage:
        return _update_appimage(dst, appimage)
    return _update_windows(dst)
