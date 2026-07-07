"""API local de Expoal + servido de la interfaz web estática."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__, config, dialogs, updater
from .downloader import DownloadManager, clean_error
from .history import History

WEB_DIR = Path(__file__).parent / "web"
VALID_MODES = {"video", "audio"}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

app = FastAPI(title="Expoal", version=__version__)
history = History(config.HISTORY_FILE)
manager = DownloadManager(history)


@app.middleware("http")
async def local_origin_guard(request: Request, call_next):
    """Bloquea escrituras cross-origin: solo la propia interfaz local puede usar la API.

    Sin esto, una web maliciosa abierta en el navegador podría lanzar POST contra
    127.0.0.1 (CSRF contra servidores locales). Los navegadores siempre mandan
    la cabecera Origin en peticiones POST.
    """
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and urlparse(origin).hostname not in LOCAL_HOSTS:
            return JSONResponse({"detail": "Origen no permitido"}, status_code=403)
    return await call_next(request)


class InfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    mode: str = "video"
    quality: str = "best"  # "best" o una altura en píxeles ("1080", "720"...)
    folder: str | None = None
    title: str = ""


def _validate_url(url: str) -> str:
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="La URL debe empezar por http:// o https://")
    return url


@app.get("/api/config")
def get_config() -> dict:
    return {
        "version": __version__,
        "default_folder": str(config.DEFAULT_DOWNLOAD_DIR),
        "ffmpeg": config.ffmpeg_available(),
    }


@app.post("/api/info")
def video_info(req: InfoRequest) -> dict:
    url = _validate_url(req.url)
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise HTTPException(status_code=422, detail=clean_error(exc)) from exc
    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise HTTPException(status_code=422, detail="El enlace no contiene ningún vídeo")
        info = entries[0]
    heights = sorted(
        {f["height"] for f in info.get("formats", []) if f.get("height")}, reverse=True
    )
    return {
        "url": url,
        "title": info.get("title", ""),
        "uploader": info.get("uploader") or info.get("channel") or "",
        "thumbnail": info.get("thumbnail", ""),
        "duration": info.get("duration"),
        "platform": info.get("extractor_key", ""),
        "heights": heights,
    }


@app.post("/api/download")
def start_download(req: DownloadRequest) -> dict:
    url = _validate_url(req.url)
    if req.mode not in VALID_MODES:
        raise HTTPException(status_code=422, detail="Modo no válido")
    if req.quality != "best" and not req.quality.isdigit():
        raise HTTPException(status_code=422, detail="Calidad no válida")
    if req.mode == "audio" and not config.ffmpeg_available():
        raise HTTPException(
            status_code=422,
            detail="Para extraer MP3 hace falta FFmpeg (winget install Gyan.FFmpeg)",
        )
    folder = (req.folder or "").strip() or str(config.DEFAULT_DOWNLOAD_DIR)
    return manager.enqueue(url, req.mode, req.quality, folder, title=req.title)


@app.post("/api/pick-folder")
def pick_folder() -> dict:
    return {"folder": dialogs.pick_folder()}


@app.get("/api/update/check")
def update_check(force: bool = False) -> dict:
    return updater.check_for_update(force=force)


@app.post("/api/update/apply")
def update_apply() -> dict:
    result = updater.apply_update()
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("error", "no se pudo actualizar"))
    return result


@app.get("/api/jobs")
def list_jobs() -> list[dict]:
    return manager.snapshot()


@app.get("/api/history")
def list_history() -> list[dict]:
    return history.entries()


@app.delete("/api/history")
def clear_history() -> dict:
    history.clear()
    return {"ok": True}


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
