"""API local de Expoal + servido de la interfaz web estática."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__, config, dialogs, engine, subtitles, updater
from .downloader import AUDIO_FORMATS, VIDEO_FORMATS, DownloadManager, clean_error
from .editor import Edits
from .history import History

WEB_DIR = Path(__file__).parent / "web"
VALID_MODES = {"video", "audio", "text"}
VALID_SUB_FORMATS = {"txt", "srt"}
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


class EditRequest(BaseModel):
    """Ediciones opcionales sobre el vídeo descargado."""

    trim_start: float | None = None
    trim_end: float | None = None
    crop_top: int = 0
    crop_bottom: int = 0
    crop_left: int = 0
    crop_right: int = 0
    mute: bool = False


class DownloadRequest(BaseModel):
    url: str
    mode: str = "video"
    quality: str = "best"  # "best" o una altura en píxeles ("1080", "720"...)
    folder: str | None = None
    title: str = ""
    edits: EditRequest | None = None
    subs: bool = False           # bajar también los subtítulos (modo vídeo)
    sub_lang: str = ""           # código de idioma
    sub_format: str = "txt"      # "txt" (texto limpio) o "srt" (con tiempos)
    out_format: str = ""         # MP4/MKV/MOV/WEBM o MP3/M4A/WAV/FLAC/OPUS


def _validate_url(url: str) -> str:
    url = url.strip()
    if not url.lower().startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="La URL debe empezar por http:// o https://")
    return url


@app.get("/api/config")
def get_config() -> dict:
    return {
        "version": __version__,
        "engine": engine.current_version(),
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
        # Dimensiones del vídeo: la interfaz las necesita para el recorte de bordes.
        "width": info.get("width") or 0,
        "height": info.get("height") or 0,
        "ffmpeg": config.ffmpeg_available(),
        # Idiomas de subtítulos disponibles (propios primero, luego automáticos).
        "subtitles": subtitles.languages(info),
        # Formatos de salida que puede producir esta instalación.
        "video_formats": sorted(VIDEO_FORMATS),
        "audio_formats": sorted(AUDIO_FORMATS),
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
    edits = None
    if req.mode == "video" and req.edits:
        e = req.edits
        edits = Edits(
            trim_start=e.trim_start,
            trim_end=e.trim_end,
            crop_top=max(0, e.crop_top),
            crop_bottom=max(0, e.crop_bottom),
            crop_left=max(0, e.crop_left),
            crop_right=max(0, e.crop_right),
            mute=e.mute,
        )
        if edits.has_any and not config.ffmpeg_available():
            raise HTTPException(
                status_code=422,
                detail="Para editar el vídeo hace falta FFmpeg (winget install Gyan.FFmpeg)",
            )
        if edits.trim_start is not None and edits.trim_end is not None:
            if edits.trim_end <= edits.trim_start:
                raise HTTPException(status_code=422, detail="El final debe ir después del inicio")
        if not edits.has_any:
            edits = None

    if req.sub_format not in VALID_SUB_FORMATS:
        raise HTTPException(status_code=422, detail="Formato de texto no válido")
    if req.mode == "text" and not req.sub_lang:
        raise HTTPException(status_code=422, detail="Elige el idioma de los subtítulos")

    out_format = (req.out_format or "").lower()
    if out_format:
        allowed = VIDEO_FORMATS if req.mode == "video" else AUDIO_FORMATS
        if req.mode != "text" and out_format not in allowed:
            raise HTTPException(status_code=422, detail="Formato de salida no válido")
        if not config.ffmpeg_available():
            raise HTTPException(
                status_code=422,
                detail="Para elegir el formato hace falta FFmpeg (winget install Gyan.FFmpeg)",
            )

    folder = (req.folder or "").strip() or str(config.DEFAULT_DOWNLOAD_DIR)
    return manager.enqueue(
        url, req.mode, req.quality, folder, title=req.title, edits=edits,
        subs=req.subs, sub_lang=req.sub_lang, sub_format=req.sub_format,
        out_format=out_format,
    )


@app.post("/api/pick-folder")
def pick_folder() -> dict:
    return {"folder": dialogs.pick_folder()}


@app.get("/api/update/check")
def update_check(force: bool = False) -> dict:
    result = dict(updater.check_for_update(force=force))
    # El motor (yt-dlp) se comprueba aparte: se renueva sin sacar versión de la app.
    result["engine"] = engine.check(force=force)
    return result


@app.post("/api/update/apply")
def update_apply() -> dict:
    result = updater.apply_update()
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("error", "no se pudo actualizar"))
    return result


ACTIVE_STATUSES = {"descargando", "procesando", "editando"}


@app.post("/api/update/engine")
def update_engine() -> dict:
    # Con una descarga en marcha no se toca el motor: sus módulos se cargan
    # perezosamente y cambiar los archivos a mitad podría romperla.
    if any(j["status"] in ACTIVE_STATUSES for j in manager.snapshot()):
        raise HTTPException(status_code=409, detail="Espera a que terminen las descargas en curso")
    result = engine.apply()
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("error", "no se pudo actualizar el motor"))
    return result


@app.get("/api/jobs")
def list_jobs() -> list[dict]:
    return manager.snapshot()


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    result = manager.cancel(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return result


@app.delete("/api/jobs")
def clear_jobs() -> dict:
    return {"removed": manager.clear_finished()}


class OpenRequest(BaseModel):
    path: str


@app.post("/api/open-folder")
def open_folder(req: OpenRequest) -> dict:
    # Solo rutas que la propia app produjo (historial o trabajos terminados):
    # nunca una arbitraria, aunque la petición venga del propio equipo.
    known = {e.get("file_path") for e in history.entries()}
    known |= {j["file_path"] for j in manager.snapshot() if j.get("file_path")}
    if req.path not in known:
        raise HTTPException(status_code=403, detail="Ruta no reconocida")
    if not Path(req.path).exists():
        raise HTTPException(status_code=404, detail="El archivo ya no está ahí")
    dialogs.reveal_in_folder(req.path)
    return {"ok": True}


@app.get("/api/history")
def list_history() -> list[dict]:
    return history.entries()


@app.delete("/api/history")
def clear_history() -> dict:
    history.clear()
    return {"ok": True}


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
