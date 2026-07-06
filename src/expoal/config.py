"""Rutas de datos y detección de dependencias externas."""
from __future__ import annotations

import shutil
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "Expoal"

DATA_DIR = Path(user_data_dir(APP_NAME, appauthor=False))
HISTORY_FILE = DATA_DIR / "history.json"
DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "Expoal"


def find_ffmpeg() -> str | None:
    """Busca ffmpeg en el PATH y, si no está, en rutas típicas de winget.

    winget añade FFmpeg al PATH de usuario, pero los procesos ya abiertos no lo ven;
    mirar directamente en su carpeta de paquetes cubre ese caso sin pedir reiniciar.
    """
    found = shutil.which("ffmpeg")
    if found:
        return found
    winget_packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_packages.is_dir():
        for pkg in winget_packages.glob("Gyan.FFmpeg*"):
            for exe in pkg.glob("**/bin/ffmpeg.exe"):
                return str(exe)
    return None


def ffmpeg_available() -> bool:
    return find_ffmpeg() is not None
