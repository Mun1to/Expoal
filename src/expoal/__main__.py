"""Entry point: web mode (browser) or desktop mode (native window)."""
from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

DEFAULT_PORT = 8710
APP_USER_MODEL_ID = "Orquio.Expoal"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_port(port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)


def _serve(port: int) -> None:
    # Import directo (no string) para que PyInstaller incluya el módulo en el .exe.
    from .server import app

    # Solo 127.0.0.1: la app nunca se expone a la red local.
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def _run_desktop() -> None:
    import webview

    if sys.platform == "win32":
        # Identidad propia en la barra de tareas (icono y agrupación correctos).
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)

    port = _free_port()
    threading.Thread(target=_serve, args=(port,), daemon=True).start()
    _wait_for_port(port)
    webview.create_window("Expoal", f"http://127.0.0.1:{port}", width=1024, height=760)
    webview.start()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="expoal",
        description="Download videos from YouTube, TikTok or Instagram to your local disk.",
    )
    parser.add_argument("--desktop", action="store_true", help="open in a native window")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="web mode port")
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser")
    args = parser.parse_args()

    if args.desktop:
        _run_desktop()
        return

    url = f"http://127.0.0.1:{args.port}"
    if sys.stdout is not None:
        # En apps empaquetadas sin consola (PyInstaller --windowed) stdout es None
        # y print() lanzaría AttributeError antes de arrancar el servidor.
        print(f"Expoal running at {url}")
    if not args.no_browser:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    _serve(args.port)


if __name__ == "__main__":
    main()
