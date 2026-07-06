"""Entry point: web mode (browser) or desktop mode (native window)."""
from __future__ import annotations

import argparse
import socket
import threading
import time
import webbrowser

import uvicorn

DEFAULT_PORT = 8710


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
    # Solo 127.0.0.1: la app nunca se expone a la red local.
    uvicorn.run("expoal.server:app", host="127.0.0.1", port=port, log_level="warning")


class _DesktopApi:
    """Funciones nativas expuestas a la interfaz cuando corre dentro de la ventana."""

    window = None

    def pick_folder(self) -> str | None:
        import webview

        result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None


def _run_desktop() -> None:
    import webview

    port = _free_port()
    threading.Thread(target=_serve, args=(port,), daemon=True).start()
    _wait_for_port(port)
    api = _DesktopApi()
    api.window = webview.create_window(
        "Expoal", f"http://127.0.0.1:{port}", width=1024, height=760, js_api=api
    )
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
    print(f"Expoal running at {url}")
    if not args.no_browser:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    _serve(args.port)


if __name__ == "__main__":
    main()
