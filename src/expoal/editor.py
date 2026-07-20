"""Post-procesado de vídeo con FFmpeg: recorte de duración, recorte de bordes y silenciado.

Se aplica DESPUÉS de que yt-dlp haya descargado el archivo. Si no hay ninguna edición
pedida, no se toca el archivo (ni se recodifica), así que el caso normal no paga coste.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Edits:
    """Ediciones pedidas desde la interfaz. Todo opcional."""

    trim_start: float | None = None   # segundos
    trim_end: float | None = None     # segundos
    crop_top: int = 0                 # píxeles a recortar por cada lado
    crop_bottom: int = 0
    crop_left: int = 0
    crop_right: int = 0
    mute: bool = False

    @property
    def has_trim(self) -> bool:
        return bool(self.trim_start) or bool(self.trim_end)

    @property
    def has_crop(self) -> bool:
        return any((self.crop_top, self.crop_bottom, self.crop_left, self.crop_right))

    @property
    def has_any(self) -> bool:
        return self.has_trim or self.has_crop or self.mute


def _crop_filter(edits: Edits, width: int, height: int) -> str:
    """Filtro crop de FFmpeg. Las dimensiones se fuerzan a pares (H.264 lo exige)."""
    out_w = width - edits.crop_left - edits.crop_right
    out_h = height - edits.crop_top - edits.crop_bottom
    out_w -= out_w % 2
    out_h -= out_h % 2
    if out_w <= 0 or out_h <= 0:
        raise ValueError("El recorte deja el vídeo sin imagen: reduce los márgenes")
    return f"crop={out_w}:{out_h}:{edits.crop_left}:{edits.crop_top}"


def build_command(src: Path, dst: Path, edits: Edits, ffmpeg: str,
                  width: int = 0, height: int = 0) -> list[str]:
    """Construye el comando de FFmpeg según lo que haya que hacer.

    Sin recorte de imagen se copian los flujos (instantáneo). Con recorte hay que
    recodificar el vídeo, así que se usa un preset rápido.
    """
    cmd = [ffmpeg, "-y", "-loglevel", "error"]

    # -ss antes de -i hace la búsqueda rápida; -to después marca el punto final.
    if edits.trim_start:
        cmd += ["-ss", f"{edits.trim_start:.3f}"]
    cmd += ["-i", str(src)]
    if edits.trim_end:
        duration = edits.trim_end - (edits.trim_start or 0)
        cmd += ["-t", f"{duration:.3f}"]

    if edits.has_crop:
        if not (width and height):
            raise ValueError("Faltan las dimensiones del vídeo para recortarlo")
        cmd += ["-vf", _crop_filter(edits, width, height)]
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
    else:
        cmd += ["-c:v", "copy"]

    if edits.mute:
        cmd += ["-an"]
    elif edits.has_crop:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-c:a", "copy"]

    # Necesario al cortar copiando flujos, para que el resultado empiece en 0.
    if edits.has_trim and not edits.has_crop:
        cmd += ["-avoid_negative_ts", "make_zero"]

    cmd.append(str(dst))
    return cmd


def apply(src: Path, edits: Edits, ffmpeg: str, width: int = 0, height: int = 0) -> Path:
    """Aplica las ediciones sobre `src` y devuelve la ruta final.

    Trabaja sobre un archivo temporal y solo sustituye el original si FFmpeg termina
    bien, para no dejar nunca al usuario con un vídeo a medias.
    """
    if not edits.has_any:
        return src

    tmp = src.with_name(f"{src.stem}.edit{src.suffix}")
    cmd = build_command(src, tmp, edits, ffmpeg, width, height)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not tmp.exists():
        tmp.unlink(missing_ok=True)
        detail = (result.stderr or "").strip().splitlines()
        raise RuntimeError(detail[-1] if detail else "FFmpeg no pudo editar el vídeo")

    src.unlink(missing_ok=True)
    tmp.rename(src)
    return src
