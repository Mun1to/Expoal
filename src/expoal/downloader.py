"""Cola de descargas: un worker secuencial que ejecuta yt-dlp y reporta progreso."""
from __future__ import annotations

import datetime as dt
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import yt_dlp

from . import config, settings, subtitles
from .editor import Edits, apply as apply_edits
from .history import History


def clean_error(exc: BaseException) -> str:
    msg = str(exc)
    if msg.startswith("ERROR:"):
        msg = msg[len("ERROR:"):].strip()
    return msg or exc.__class__.__name__


class JobCancelled(Exception):
    """El usuario canceló el trabajo; no es un error."""


# Opciones que las avanzadas NO pueden pisar, porque son las que sostienen la
# app: sin el hook no hay progreso ni forma de cancelar, y sin el modo callado
# yt-dlp escribe en una salida que nadie lee.
_PROTECTED_OPTS = ("progress_hooks", "quiet", "no_warnings", "noprogress")


def _apply_extra_opts(opts: dict) -> None:
    """Mezcla las opciones avanzadas del usuario sobre las de la app, en el sitio.

    Se hace al final y en este orden a propósito: lo que escribe el usuario gana
    (para eso es una válvula de escape y puede querer cambiar el formato), salvo
    lo que rompería la app. Los postprocesadores se SUMAN en vez de sustituirse:
    si no, pedir "incrusta la miniatura" borraría la extracción de audio y el
    MP3 saldría siendo un MP4.
    """
    extra = settings.extra_opts()
    if not extra:
        return
    mine = [dict(p) for p in opts.get("postprocessors") or []]
    theirs = [dict(p) for p in extra.get("postprocessors") or []]
    protected = {k: opts[k] for k in _PROTECTED_OPTS if k in opts}
    opts.update(extra)
    opts.update(protected)
    if mine or theirs:
        opts["postprocessors"] = mine + theirs


# Formatos de salida que ofrecemos. Los de vídeo se obtienen remuxeando (cambiar el
# envoltorio sin tocar los datos, casi instantáneo) salvo WEBM, que obliga a recodificar
# porque necesita códecs distintos. Los de audio los produce FFmpeg al extraer.
VIDEO_FORMATS = {"mp4", "mkv", "mov", "webm"}
AUDIO_FORMATS = {"mp3", "m4a", "wav", "flac", "opus"}


def _format_selector(mode: str, quality: str, has_ffmpeg: bool, out_format: str = "") -> str:
    if mode == "audio":
        return "ba/b"
    cap = f"[height<={quality}]" if quality != "best" else ""
    if not has_ffmpeg:
        # Sin ffmpeg no se puede fusionar: solo archivos ya completos
        # (suele limitar a 720p en YouTube).
        return f"b{cap}/b"

    # El contenedor manda sobre el códec. YouTube sirve AV1 en muchas calidades, y AV1
    # no cabe en un MOV: si no lo pedimos compatible, el remux falla. Con MKV da igual
    # (admite de todo) y con WEBM preferimos sus códecs nativos para no recodificar.
    if out_format == "mov":
        return (
            f"bv*[vcodec^=avc1]{cap}+ba[acodec^=mp4a]/"
            f"bv*[vcodec^=avc1]{cap}+ba/b[vcodec^=avc1]{cap}/b{cap}"
        )
    if out_format == "webm":
        return f"bv*[ext=webm]{cap}+ba[ext=webm]/bv*{cap}+ba/b{cap}"

    # Mejor vídeo + mejor audio fusionados; si no hay streams separados, el mejor archivo único.
    return f"bv*{cap}+ba/b{cap}"


def _fmt_speed(speed: float | None) -> str:
    if not speed:
        return ""
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if speed < 1024:
            return f"{speed:.1f} {unit}"
        speed /= 1024
    return f"{speed:.1f} TB/s"


def _fmt_eta(eta: float | None) -> str:
    if not eta:
        return ""
    eta = int(eta)
    if eta >= 3600:
        return f"{eta // 3600}h {(eta % 3600) // 60}m"
    if eta >= 60:
        return f"{eta // 60}m {eta % 60}s"
    return f"{eta}s"


def _find_subtitle(info: dict, folder: Path) -> Path | None:
    """Localiza el archivo de subtítulos que acaba de escribir yt-dlp."""
    requested = info.get("requested_subtitles") or {}
    for track in requested.values():
        path = (track or {}).get("filepath")
        if path and Path(path).exists():
            return Path(path)
    # Respaldo: buscar por el id del vídeo en la carpeta de destino.
    video_id = info.get("id") or ""
    if video_id:
        for ext in ("srt", "vtt"):
            matches = sorted(folder.glob(f"*[[]{video_id}[]]*.{ext}"))
            if matches:
                return matches[0]
    return None


def _final_path(info: dict) -> str:
    requested = info.get("requested_downloads") or []
    if requested and requested[0].get("filepath"):
        return requested[0]["filepath"]
    return info.get("filepath") or ""


@dataclass
class Job:
    id: str
    url: str
    mode: str
    quality: str
    folder: str
    title: str = ""
    edits: Edits | None = None
    subs: bool = False          # descargar también los subtítulos (modo vídeo)
    sub_lang: str = ""          # código de idioma de los subtítulos
    sub_format: str = "txt"     # "txt" (texto limpio) o "srt" (con tiempos)
    out_format: str = ""        # contenedor de vídeo o códec de audio pedido
    status: str = "en_cola"  # en_cola | descargando | procesando | editando | completado | error | cancelado
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error: str = ""
    file_path: str = ""
    created_at: float = field(default_factory=time.time)
    # Cancelación: el hook de progreso mira este evento en cada tick y aborta.
    cancel_event: threading.Event = field(default_factory=threading.Event)
    # Archivos en curso, para poder borrar los restos (.part) al cancelar.
    current_file: str = ""
    current_tmp: str = ""

    def public(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "mode": self.mode,
            "quality": self.quality,
            "title": self.title,
            "status": self.status,
            "progress": self.progress,
            "speed": self.speed,
            "eta": self.eta,
            "error": self.error,
            # Un fallo por falta de sesión tiene arreglo (elegir navegador), así
            # que la interfaz lo trata distinto de un error cualquiera.
            "needs_cookies": bool(self.error) and settings.looks_like_login_error(self.error),
            "file_path": self.file_path,
        }


class DownloadManager:
    def __init__(self, history: History):
        self._history = history
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []
        self._queue: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def enqueue(self, url: str, mode: str, quality: str, folder: str, title: str = "",
                edits: Edits | None = None, subs: bool = False, sub_lang: str = "",
                sub_format: str = "txt", out_format: str = "") -> dict:
        job = Job(
            id=uuid.uuid4().hex[:12],
            url=url,
            mode=mode,
            quality=quality,
            folder=folder,
            title=title,
            edits=edits,
            subs=subs,
            sub_lang=sub_lang,
            sub_format=sub_format,
            out_format=out_format,
        )
        with self._lock:
            self._jobs[job.id] = job
            self._order.append(job.id)
        self._queue.put(job.id)
        return job.public()

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [self._jobs[job_id].public() for job_id in reversed(self._order)]

    def cancel(self, job_id: str) -> dict | None:
        """Cancela un trabajo en cola o descargando. Devuelve None si no existe."""
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.status == "en_cola":
            job.cancel_event.set()
            job.status = "cancelado"
        elif job.status == "descargando":
            # El hook de progreso lo verá en el siguiente tick y abortará.
            job.cancel_event.set()
        # procesando/editando ya no se cancelan: FFmpeg está en plena escritura.
        return job.public()

    TERMINAL = {"completado", "error", "cancelado"}

    def clear_finished(self) -> int:
        """Quita de la lista los trabajos ya terminados (en cualquier sentido)."""
        with self._lock:
            keep = [jid for jid in self._order if self._jobs[jid].status not in self.TERMINAL]
            removed = len(self._order) - len(keep)
            self._jobs = {jid: self._jobs[jid] for jid in keep}
            self._order = keep
        return removed

    def _run(self) -> None:
        while True:
            job_id = self._queue.get()
            try:
                # .get(): el trabajo puede haber salido de la lista con "Limpiar"
                # mientras esperaba en la cola.
                job = self._jobs.get(job_id)
                if job is None or job.cancel_event.is_set():
                    if job is not None:
                        job.status = "cancelado"
                    continue
                self._download(job)
            except Exception as exc:  # noqa: BLE001 - el worker nunca debe morir
                if job.cancel_event.is_set():
                    # yt-dlp envuelve la excepción del hook, así que se clasifica
                    # por el evento y no por el tipo que llegue hasta aquí.
                    job.status = "cancelado"
                    job.error = ""
                    job.speed = ""
                    job.eta = ""
                    self._cleanup_partial(job)
                else:
                    job.status = "error"
                    job.error = clean_error(exc)
            finally:
                self._queue.task_done()

    @staticmethod
    def _cleanup_partial(job: Job) -> None:
        """Borra los restos de una descarga cancelada (.part y compañía)."""
        for name in (job.current_tmp, job.current_file):
            if not name:
                continue
            for path in (Path(name), Path(name + ".part"), Path(name + ".ytdl")):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass  # un resto bloqueado no debe tumbar el worker

    def _download(self, job: Job) -> None:
        folder = Path(job.folder).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        ffmpeg_path = config.find_ffmpeg()
        has_ffmpeg = ffmpeg_path is not None
        job.status = "descargando"

        def hook(d: dict) -> None:
            if job.cancel_event.is_set():
                raise JobCancelled("cancelado por el usuario")
            # Se apuntan los archivos en curso para poder limpiar al cancelar.
            if d.get("tmpfilename"):
                job.current_tmp = d["tmpfilename"]
            if d.get("filename"):
                job.current_file = d["filename"]
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                if total:
                    job.progress = round(d.get("downloaded_bytes", 0) * 100 / total, 1)
                job.speed = _fmt_speed(d.get("speed"))
                job.eta = _fmt_eta(d.get("eta"))
            elif d["status"] == "finished":
                job.progress = 100.0
                job.speed = ""
                job.eta = ""
                job.status = "procesando"

        opts: dict = {
            "format": _format_selector(job.mode, job.quality, has_ffmpeg, job.out_format),
            # La carpeta va en "paths" y NO dentro de outtmpl. Parece lo mismo,
            # pero no lo es: si la ruta viviera en la plantilla, un usuario que
            # pusiera su propio "-o" en las opciones avanzadas la borraría sin
            # querer y el archivo acabaría en donde se lanzó la app. Separadas,
            # puede cambiar el nombre sin perder la carpeta que eligió.
            "paths": {"home": str(folder)},
            "outtmpl": "%(title)s [%(id)s].%(ext)s",
            "noplaylist": True,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "progress_hooks": [hook],
            # Cookies del navegador si el usuario eligió uno: es lo que
            # desbloquea privados, con edad restringida y los anti-bot.
            **settings.cookie_opts(),
        }
        if has_ffmpeg:
            opts["ffmpeg_location"] = ffmpeg_path
        if job.mode == "video" and has_ffmpeg:
            container = job.out_format if job.out_format in VIDEO_FORMATS else "mp4"
            opts["merge_output_format"] = container
            if container != "mp4":
                # Cambia el envoltorio al pedido; si los códecs no caben dentro
                # (caso de WEBM), yt-dlp recodifica por su cuenta.
                opts["postprocessors"] = [
                    {"key": "FFmpegVideoRemuxer", "preferedformat": container}
                ]
        if job.mode == "audio" and has_ffmpeg:
            codec = job.out_format if job.out_format in AUDIO_FORMATS else "mp3"
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": codec,
                    "preferredquality": "192",
                }
            ]

        # Subtítulos: en modo "texto" solo se bajan ellos; en vídeo pueden ir de acompañantes.
        wants_subs = job.mode == "text" or job.subs
        if wants_subs:
            lang = job.sub_lang or "en"
            opts.update(
                {
                    "writesubtitles": True,
                    "writeautomaticsub": True,  # respaldo si no hay subtítulos propios
                    "subtitleslangs": [lang],
                    "subtitlesformat": "srt/vtt/best",
                }
            )
            if job.mode == "text":
                opts["skip_download"] = True
                opts["format"] = None

        _apply_extra_opts(opts)

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(job.url, download=True)

        job.title = job.title or info.get("title") or job.url
        job.file_path = _final_path(info)

        # Subtítulos: yt-dlp los deja como "<nombre>.<idioma>.srt" junto al vídeo.
        if wants_subs:
            sub_file = _find_subtitle(info, folder)
            if not sub_file:
                if job.mode == "text":
                    raise RuntimeError("Este vídeo no tiene subtítulos disponibles")
            elif job.sub_format == "txt":
                text = subtitles.to_text(sub_file)
                txt_file = sub_file.with_suffix(".txt")
                txt_file.write_text(text, encoding="utf-8")
                sub_file.unlink(missing_ok=True)
                sub_file = txt_file
            if sub_file and job.mode == "text":
                job.file_path = str(sub_file)

        # Ediciones (recorte de duración, recorte de bordes, silenciar) sobre el archivo ya
        # descargado. Solo aplica a vídeo: en modo audio no tienen sentido.
        if job.mode == "video" and job.edits and job.edits.has_any and job.file_path:
            if not has_ffmpeg:
                raise RuntimeError("Para editar el vídeo hace falta FFmpeg")
            job.status = "editando"
            job.progress = 100.0
            apply_edits(
                Path(job.file_path),
                job.edits,
                ffmpeg_path,
                width=info.get("width") or 0,
                height=info.get("height") or 0,
            )

        job.status = "completado"
        job.progress = 100.0
        self._history.add(
            {
                "url": job.url,
                "title": job.title,
                "platform": info.get("extractor_key", ""),
                "mode": job.mode,
                "quality": job.quality,
                "file_path": job.file_path,
                "downloaded_at": dt.datetime.now().isoformat(timespec="seconds"),
            }
        )
