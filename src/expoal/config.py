"""Rutas de datos y detección de dependencias externas."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "Expoal"

DATA_DIR = Path(user_data_dir(APP_NAME, appauthor=False))
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "Expoal"


def _next_to_app(name: str) -> str | None:
    """Busca un binario en la carpeta de la propia app.

    Es la vía sin instalación ni PATH: dejar el .exe al lado de Expoal.exe y
    listo. Con PyInstaller, sys.executable ES la app; ejecutando desde el código
    fuente no aplica, pero mirar no cuesta nada.
    """
    folder = Path(sys.executable).parent
    for candidate in (folder / name, folder / f"{name}.exe"):
        if candidate.is_file():
            return str(candidate)
    return None


def _winget_binary(package: str, name: str) -> str | None:
    """Busca un binario en la carpeta de paquetes de winget.

    winget añade sus programas al PATH de usuario, pero los procesos ya abiertos
    conservan su copia del entorno y no lo ven. Mirar directamente en su carpeta
    cubre ese caso sin pedirle a nadie que reinicie nada.
    """
    packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if not packages.is_dir():
        return None
    for pkg in packages.glob(f"{package}*"):
        for exe in pkg.glob(f"**/bin/{name}.exe"):
            return str(exe)
        # Algunos paquetes no usan subcarpeta bin.
        for exe in pkg.glob(f"**/{name}.exe"):
            return str(exe)
    return None


def find_ffmpeg() -> str | None:
    """Busca ffmpeg en el PATH, junto a la app y en rutas típicas de winget."""
    return shutil.which("ffmpeg") or _next_to_app("ffmpeg") or _winget_binary("Gyan.FFmpeg", "ffmpeg")


def ffmpeg_available() -> bool:
    return find_ffmpeg() is not None


def find_aria2c() -> str | None:
    """Busca aria2c, el descargador multi-conexión opcional.

    No viene con Expoal ni se descarga solo: es un binario de terceros y bajarlo
    a espaldas del usuario sería justo lo contrario de lo que promete la app. Si
    lo tiene instalado (o lo deja al lado del .exe), se le ofrece usarlo.
    """
    return shutil.which("aria2c") or _next_to_app("aria2c") or _winget_binary("aria2.aria2", "aria2c")


def aria2c_available() -> bool:
    return find_aria2c() is not None
