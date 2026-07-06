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

from . import config
from .history import History


def clean_error(exc: BaseException) -> str:
    msg = str(exc)
    if msg.startswith("ERROR:"):
        msg = msg[len("ERROR:"):].strip()
    return msg or exc.__class__.__name__


def _format_selector(mode: str, quality: str, has_ffmpeg: bool) -> str:
    if mode == "audio":
        return "ba/b"
    cap = f"[height<={quality}]" if quality != "best" else ""
    if has_ffmpeg:
        # Mejor vídeo + mejor audio fusionados; si no hay streams separados, el mejor archivo único.
        return f"bv*{cap}+ba/b{cap}"
    # Sin ffmpeg no se puede fusionar: solo archivos ya completos (suele limitar a 720p en YouTube).
    return f"b{cap}/b"


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
    status: str = "en_cola"  # en_cola | descargando | procesando | completado | error
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error: str = ""
    file_path: str = ""
    created_at: float = field(default_factory=time.time)

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

    def enqueue(self, url: str, mode: str, quality: str, folder: str, title: str = "") -> dict:
        job = Job(
            id=uuid.uuid4().hex[:12],
            url=url,
            mode=mode,
            quality=quality,
            folder=folder,
            title=title,
        )
        with self._lock:
            self._jobs[job.id] = job
            self._order.append(job.id)
        self._queue.put(job.id)
        return job.public()

    def snapshot(self) -> list[dict]:
        with self._lock:
            return [self._jobs[job_id].public() for job_id in reversed(self._order)]

    def _run(self) -> None:
        while True:
            job_id = self._queue.get()
            job = self._jobs[job_id]
            try:
                self._download(job)
            except Exception as exc:  # noqa: BLE001 - el worker nunca debe morir
                job.status = "error"
                job.error = clean_error(exc)
            finally:
                self._queue.task_done()

    def _download(self, job: Job) -> None:
        folder = Path(job.folder).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        ffmpeg_path = config.find_ffmpeg()
        has_ffmpeg = ffmpeg_path is not None
        job.status = "descargando"

        def hook(d: dict) -> None:
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
            "format": _format_selector(job.mode, job.quality, has_ffmpeg),
            "outtmpl": str(folder / "%(title)s [%(id)s].%(ext)s"),
            "noplaylist": True,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "progress_hooks": [hook],
        }
        if has_ffmpeg:
            opts["ffmpeg_location"] = ffmpeg_path
        if job.mode == "video" and has_ffmpeg:
            opts["merge_output_format"] = "mp4"
        if job.mode == "audio" and has_ffmpeg:
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(job.url, download=True)

        job.title = job.title or info.get("title") or job.url
        job.file_path = _final_path(info)
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
