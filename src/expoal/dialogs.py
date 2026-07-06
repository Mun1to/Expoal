"""Diálogo nativo de selección de carpeta.

En modo escritorio usa el diálogo de la ventana pywebview. En modo web lanza un
subproceso de Python con tkinter (diálogo moderno de Windows en Tk 8.6+); un
subproceso evita los problemas de tkinter fuera del hilo principal. En una app
congelada (PyInstaller) sin ventana no hay subproceso de Python disponible, así
que devuelve None y la interfaz mantiene el cuadro de texto como alternativa.
"""
from __future__ import annotations

import subprocess
import sys
import threading

_lock = threading.Lock()

_TK_SCRIPT = (
    "import tkinter as tk\n"
    "from tkinter import filedialog\n"
    "root = tk.Tk()\n"
    "root.withdraw()\n"
    "root.attributes('-topmost', True)\n"
    "print(filedialog.askdirectory(title='Expoal: carpeta de destino') or '')\n"
)


def pick_folder() -> str | None:
    with _lock:
        try:
            import webview

            if webview.windows:
                result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
                return result[0] if result else None
        except Exception:  # noqa: BLE001 - si el modo escritorio falla, probamos tkinter
            pass

        if getattr(sys, "frozen", False):
            return None

        try:
            result = subprocess.run(
                [sys.executable, "-c", _TK_SCRIPT],
                capture_output=True,
                text=True,
                timeout=300,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        folder = (result.stdout or "").strip()
        return folder or None
