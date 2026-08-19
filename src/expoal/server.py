"""API local de Expoal + servido de la interfaz web estática."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__, config, dialogs, engine, logbus, settings, subtitles, updater, urls
from .downloader import (AUDIO_FORMATS, VIDEO_FORMATS, DownloadManager, clean_error,
                         format_selector)
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


class CookiesRequest(BaseModel):
    browser: str = ""


class CookiesFileRequest(BaseModel):
    path: str = ""


class UrlsRequest(BaseModel):
    text: str = ""


class ArgsRequest(BaseModel):
    args: str = ""


class ToggleRequest(BaseModel):
    name: str
    value: bool = False


class BatchItem(BaseModel):
    url: str
    title: str = ""


class BatchRequest(BaseModel):
    items: list[BatchItem] = []
    mode: str = "video"
    quality: str = "best"
    folder: str = ""
    out_format: str = ""


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


def _folder_for(requested: str | None) -> str:
    """La carpeta de destino de una descarga, recordada para la próxima vez.

    Se guarda aquí, en el único sitio por el que pasan todas las descargas, en
    vez de al elegirla en el explorador: lo que hay que recordar es dónde se
    guardó de verdad, no dónde se estuvo mirando.
    """
    folder = (requested or "").strip() or str(config.DEFAULT_DOWNLOAD_DIR)
    settings.set_download_folder(folder)
    return folder


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
        # La última que usó el usuario; si aún no hay ninguna guardada, la del
        # historial (para quien ya tenía Expoal antes de esto), y solo si no hay
        # nada de nada, la de fábrica.
        "default_folder": (
            settings.download_folder()
            or history.last_folder()
            or str(config.DEFAULT_DOWNLOAD_DIR)
        ),
        "ffmpeg": config.ffmpeg_available(),
        "aria2c": config.aria2c_available(),
        "cookies_browser": settings.cookies_browser(),
        "cookies_file": settings.cookies_file(),
        "browsers": list(settings.BROWSERS),
        "extra_args": settings.extra_args(),
        "toggles": settings.toggles(),
        # Cómo vienen de fábrica. La interfaz lo necesita para saber si el
        # usuario ha cambiado algo: el panel de opciones se abre solo cuando hay
        # algo puesto, y una casilla que viene marcada de serie no cuenta como
        # "puesto por alguien" (si contara, la pantalla ya no nacería simple).
        "toggles_default": {name: settings.default_of(name) for name in settings.TOGGLES},
        "toggles_need_ffmpeg": sorted(settings.TOGGLES_NEED_FFMPEG),
        "toggles_need_aria2c": sorted(settings.TOGGLES_NEED_ARIA2C),
    }


@app.post("/api/settings/toggle")
def set_toggle(req: ToggleRequest) -> dict:
    """Activa o desactiva una de las casillas de opciones comunes."""
    try:
        value = settings.set_toggle(req.name, req.value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"name": req.name, "value": value}


@app.post("/api/settings/cookies")
def set_cookies(req: CookiesRequest) -> dict:
    """Elige de qué navegador tomar las cookies. Cadena vacía las desactiva."""
    try:
        name = settings.set_cookies_browser(req.browser)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    # El archivo se descarta al elegir navegador: la interfaz necesita saberlo
    # para no seguir enseñando una ruta que ya no se usa.
    return {"cookies_browser": name, "cookies_file": settings.cookies_file()}


@app.post("/api/settings/cookies-file")
def set_cookies_file(req: CookiesFileRequest) -> dict:
    """Guarda un archivo cookies.txt exportado. Cadena vacía lo quita."""
    try:
        path = settings.set_cookies_file(req.path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"cookies_file": path, "cookies_browser": settings.cookies_browser()}


@app.post("/api/settings/args")
def set_args(req: ArgsRequest) -> dict:
    """Guarda las opciones avanzadas de yt-dlp, validándolas antes.

    Devuelve además un resumen de lo que hacen: enseñar al usuario que su texto
    se ha entendido (y en qué se traduce) evita el "lo escribí y no sé si vale".
    """
    try:
        text = settings.set_extra_args(req.args)
        opts = settings.parse_extra_args(text)
    except settings.ArgsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"extra_args": text, "applied": sorted(opts.keys())}


# Tope de vídeos que se leen de una playlist. Un canal puede tener miles; una
# lista de casillas con miles de filas no la usa nadie y la extracción tardaría.
# Con este límite la lista carga rápido y, si se alcanza, se avisa de que hay más.
PLAYLIST_LIMIT = 200


def _format_size(fmt: dict, duration: float) -> int:
    """Lo que ocupa un formato. Si no lo dice, se calcula con su bitrate."""
    size = fmt.get("filesize") or fmt.get("filesize_approx") or 0
    if not size and fmt.get("tbr") and duration:
        size = int(fmt["tbr"] * 1000 / 8 * duration)      # tbr viene en kbit/s
    return int(size or 0)


def sizes_by_quality(info: dict) -> dict[str, int]:
    """Cuánto ocupa cada calidad del desplegable, en bytes.

    POR QUÉ: "mejor calidad" en un vídeo de doce horas son 114 GB, y la app no
    lo decía en ninguna parte; se pulsa pensando en un vídeo normal y se
    descubre media hora después. El dato ya viene en el análisis, así que no
    cuesta ni una petición más.

    Quién elige NO lo decide esta función: se le pregunta al propio yt-dlp con
    el MISMO selector con el que se va a descargar, porque adivinarlo mintió de
    verdad al probarlo (el de más bitrate daba 32 GB donde la descarga real
    ocupaba 22: yt-dlp prefiere el códec más eficiente, no el más gordo). Se
    calcula sobre MP4, que es el caso normal; cambiar de contenedor mueve el
    número un poco. Si algo falla, se devuelve lo que haya: una calidad sin
    número es mejor que un número inventado.
    """
    formats = info.get("formats") or []
    duration = info.get("duration") or 0
    if not formats:
        return {}
    sizes: dict[str, int] = {}
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            for quality in ["best", *(str(h) for h in video_heights(info))]:
                spec = format_selector("video", quality, True, "mp4")
                try:
                    elegido = next(
                        iter(ydl.build_format_selector(spec)(
                            {"formats": formats, "incomplete_formats": {}})),
                        None,
                    )
                except Exception:  # noqa: BLE001 - esa calidad se queda sin número
                    continue
                if not elegido:
                    continue
                partes = elegido.get("requested_formats") or [elegido]
                total = sum(_format_size(f, duration) for f in partes)
                if total:
                    sizes[quality] = total
    except Exception:  # noqa: BLE001 - el peso es un extra, nunca un motivo de fallo
        return sizes
    return sizes


def video_heights(info: dict) -> list[int]:
    """Las calidades que se pueden ofrecer: solo las que son VÍDEO de verdad.

    YouTube mezcla en la lista de formatos sus storyboards (las miniaturas que
    salen al pasar el ratón por la barra de progreso): llegan con altura 27, 45
    y 90 y sin códec de vídeo. Sin filtrarlas, el desplegable de calidad
    ofrecía tres opciones que no son un vídeo, y elegir una daba siempre
    "Requested format is not available" (reproducido antes de arreglarlo).
    """
    return sorted(
        {
            f["height"] for f in info.get("formats", [])
            if f.get("height") and f.get("vcodec") and f["vcodec"] != "none"
        },
        reverse=True,
    )


@app.post("/api/info")
def video_info(req: InfoRequest) -> dict:
    url = _validate_url(req.url)
    opts = {
        "quiet": True,
        "no_warnings": True,
        # noplaylist=True es la clave del "sin sustos": un enlace de vídeo que
        # lleva &list=... (una lista de reproducción de fondo) se lee como un
        # vídeo suelto, no como la lista entera. Solo un enlace que ES una lista
        # (o un canal) vuelve como playlist.
        "noplaylist": True,
        # in_playlist lee las entradas en modo ligero (título e id, sin sondear
        # cada vídeo), así una lista de 200 carga en un momento. Un vídeo suelto
        # sí trae sus formatos completos, comprobado.
        "extract_flat": "in_playlist",
        "playlistend": PLAYLIST_LIMIT,
        **settings.cookie_opts(),
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        # Un fallo por falta de sesión no es lo mismo que un vídeo roto: la
        # interfaz necesita distinguirlos para poder ofrecer las cookies en vez
        # de dejar al usuario con un error que no sabe cómo arreglar.
        message = clean_error(exc)
        raise HTTPException(
            status_code=422,
            detail={
                "message": message,
                "needs_cookies": settings.looks_like_login_error(message),
                "cookie_error": settings.looks_like_cookie_error(message),
            },
        ) from exc

    if info.get("_type") == "playlist":
        entries = [e for e in (info.get("entries") or []) if e and e.get("url")]
        if not entries:
            raise HTTPException(status_code=422, detail="El enlace no contiene ningún vídeo")
        return {
            "type": "playlist",
            "title": info.get("title") or "",
            "uploader": info.get("uploader") or info.get("channel") or "",
            "count": len(entries),
            # Si la lista trajo justo el tope, es que había más y se cortó.
            "truncated": len(entries) >= PLAYLIST_LIMIT,
            "entries": [
                {
                    "url": e["url"],
                    "title": e.get("title") or e["url"],
                    "duration": e.get("duration"),
                }
                for e in entries
            ],
            "ffmpeg": config.ffmpeg_available(),
            "video_formats": sorted(VIDEO_FORMATS),
            "audio_formats": sorted(AUDIO_FORMATS),
        }

    heights = video_heights(info)
    return {
        "type": "video",
        "url": url,
        "title": info.get("title", ""),
        "uploader": info.get("uploader") or info.get("channel") or "",
        "thumbnail": info.get("thumbnail", ""),
        "duration": info.get("duration"),
        "platform": info.get("extractor_key", ""),
        "heights": heights,
        # Lo que ocupa cada calidad: el desplegable lo enseña para que nadie
        # pida 114 GB sin enterarse (ver sizes_by_quality).
        "sizes": sizes_by_quality(info),
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


def edits_for(mode: str, e: "EditRequest") -> Edits:
    """Las ediciones que tienen sentido en ese modo.

    En audio solo se recorta la duración: recortar bordes no tiene imagen que
    recortar, y quitarle el sonido a un sonido deja el archivo vacío. Se ignoran
    en vez de rechazar la petición, porque no son un error de quien la manda
    sino algo que la interfaz ni siquiera enseña en ese modo.
    """
    solo_audio = mode == "audio"
    return Edits(
        trim_start=e.trim_start,
        trim_end=e.trim_end,
        crop_top=0 if solo_audio else max(0, e.crop_top),
        crop_bottom=0 if solo_audio else max(0, e.crop_bottom),
        crop_left=0 if solo_audio else max(0, e.crop_left),
        crop_right=0 if solo_audio else max(0, e.crop_right),
        mute=False if solo_audio else e.mute,
    )


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
    if req.mode in ("video", "audio") and req.edits:
        edits = edits_for(req.mode, req.edits)
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

    folder = _folder_for(req.folder)
    return manager.enqueue(
        url, req.mode, req.quality, folder, title=req.title, edits=edits,
        subs=req.subs, sub_lang=req.sub_lang, sub_format=req.sub_format,
        out_format=out_format,
    )


@app.post("/api/download-batch")
def start_batch(req: BatchRequest) -> dict:
    """Encola de golpe los vídeos elegidos de una playlist, con opciones comunes.

    Reusa la misma cola que un vídeo suelto: cada elemento es un trabajo normal,
    solo que comparten formato, calidad y carpeta. Sin edición por vídeo (no
    tiene sentido el mismo recorte en 30 vídeos distintos) y sin modo texto
    (elegir idioma de subtítulos para una lista entera es una rareza).
    """
    if req.mode not in {"video", "audio"}:
        raise HTTPException(status_code=422, detail="Modo no válido para una lista")
    if req.quality != "best" and not req.quality.isdigit():
        raise HTTPException(status_code=422, detail="Calidad no válida")
    if req.mode == "audio" and not config.ffmpeg_available():
        raise HTTPException(
            status_code=422,
            detail="Para extraer MP3 hace falta FFmpeg (winget install Gyan.FFmpeg)",
        )
    out_format = (req.out_format or "").lower()
    if out_format:
        allowed = VIDEO_FORMATS if req.mode == "video" else AUDIO_FORMATS
        if out_format not in allowed:
            raise HTTPException(status_code=422, detail="Formato de salida no válido")
        if not config.ffmpeg_available():
            raise HTTPException(
                status_code=422,
                detail="Para elegir el formato hace falta FFmpeg (winget install Gyan.FFmpeg)",
            )

    items = [it for it in req.items if (it.url or "").strip()]
    if not items:
        raise HTTPException(status_code=422, detail="No has elegido ningún vídeo")
    if len(items) > PLAYLIST_LIMIT:
        raise HTTPException(status_code=422, detail=f"Máximo {PLAYLIST_LIMIT} vídeos de una vez")

    folder = _folder_for(req.folder)
    for it in items:
        _validate_url(it.url)
    queued = [
        manager.enqueue(
            it.url, req.mode, req.quality, folder,
            title=(it.title or "").strip(), out_format=out_format,
        )
        for it in items
    ]
    return {"queued": len(queued)}


@app.post("/api/urls/clean")
def clean_url_list(req: UrlsRequest) -> dict:
    """Ordena una lista de enlaces pegada a mano: quita basura y duplicados.

    Se hace en el servidor (y no en el navegador) para que sea la MISMA limpieza
    que se puede probar con tests y reutilizar desde cualquier sitio.
    """
    return urls.clean_urls(req.text)


@app.post("/api/pick-folder")
def pick_folder() -> dict:
    return {"folder": dialogs.pick_folder()}


@app.post("/api/pick-file")
def pick_file() -> dict:
    return {"path": dialogs.pick_file()}


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


@app.post("/api/jobs/retry-failed")
def retry_failed_jobs() -> dict:
    """Reencola de una vez todo lo que falló: el caso de la lista larga."""
    return {"retried": manager.retry_failed()}


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    result = manager.cancel(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return result


@app.post("/api/jobs/{job_id}/pause")
def pause_job(job_id: str) -> dict:
    result = manager.pause(job_id, True)
    if result is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return result


@app.post("/api/jobs/{job_id}/resume")
def resume_job(job_id: str) -> dict:
    result = manager.pause(job_id, False)
    if result is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return result


@app.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict:
    result = manager.retry(job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return result


@app.delete("/api/jobs")
def clear_jobs() -> dict:
    return {"removed": manager.clear_finished()}


@app.get("/api/log")
def get_log(after: int = 0) -> dict:
    """Lo que va diciendo el motor, para el panel de terminal de la interfaz.

    Con cursor: el cliente manda por dónde iba y recibe solo lo nuevo, así el
    sondeo es barato aunque el panel esté abierto todo el rato.
    """
    return logbus.bus.since(after)


@app.delete("/api/log")
def clear_log() -> dict:
    logbus.bus.clear()
    return {"ok": True}


class OpenRequest(BaseModel):
    path: str


@app.post("/api/open-folder")
def open_folder(req: OpenRequest) -> dict:
    # Solo rutas que la propia app produjo (historial o trabajos terminados):
    # nunca una arbitraria, aunque la petición venga del propio equipo.
    known = {e.get("file_path") for e in history.entries() if e.get("file_path")}
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
