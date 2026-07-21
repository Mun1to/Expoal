"""Subtítulos: qué idiomas tiene un vídeo y cómo pasarlos a texto legible.

yt-dlp entrega los subtítulos en formatos con marcas de tiempo (SRT/VTT). Para el
modo "solo texto" los limpiamos y dejamos la transcripción corrida, sin tiempos ni
etiquetas, quitando además las líneas repetidas que generan los subtítulos
automáticos (van repitiendo la frase anterior a medida que avanzan).
"""
from __future__ import annotations

import re
from pathlib import Path

# Marcas de tiempo de SRT ("00:00:01,000 --> 00:00:04,000") y de VTT (con punto).
TIMECODE = re.compile(r"^\d{1,2}:\d{2}:\d{2}[.,]\d{3}\s*-->")
TAGS = re.compile(r"<[^>]+>")           # <c>, <00:00:01.000>, etc.
CUE_SETTINGS = re.compile(r"\s+(align|position|size|line):\S+")
VTT_HEADERS = ("WEBVTT", "Kind:", "Language:", "NOTE", "STYLE")


def languages(info: dict) -> list[dict]:
    """Idiomas de subtítulos disponibles, propios primero y automáticos después."""
    out: list[dict] = []
    seen: set[str] = set()
    for source, automatic in (("subtitles", False), ("automatic_captions", True)):
        for code, tracks in (info.get(source) or {}).items():
            if code in seen or not tracks:
                continue
            seen.add(code)
            name = (tracks[0] or {}).get("name") or code
            out.append({"code": code, "name": name, "automatic": automatic})
    # Primero los manuales (mejor calidad), luego el resto por código.
    out.sort(key=lambda t: (t["automatic"], t["code"]))
    return out


def to_text(path: Path) -> str:
    """Convierte un .srt/.vtt en texto corrido sin tiempos ni repeticiones."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.isdigit() or TIMECODE.match(line):
            continue
        if any(line.startswith(h) for h in VTT_HEADERS):
            continue
        line = CUE_SETTINGS.sub("", TAGS.sub("", line)).strip()
        if not line:
            continue
        # Los subtítulos automáticos repiten la línea previa en cada fotograma.
        if lines and line == lines[-1]:
            continue
        lines.append(line)

    # Une las frases y deja párrafos legibles en vez de una línea por subtítulo.
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"(?<=[.!?])\s+", "\n", text)
