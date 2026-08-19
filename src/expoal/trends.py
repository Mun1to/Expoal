"""Qué se está moviendo ahora mismo sobre un tema, para poder bajarlo.

POR QUÉ ESTÁ EN UN DESCARGADOR: la pregunta "¿qué está petando esta semana en
lo mío?" acaba siempre en lo mismo, abrir la plataforma, buscar a mano, ordenar
como se pueda y copiar enlaces uno a uno. Expoal ya sabe hacer la segunda mitad
(coger un enlace y dejarte el vídeo en el disco), así que aquí se resuelve la
primera y las dos se juntan en una pantalla.

CÓMO, Y ESTO NO ES UN DETALLE: se le pide a la plataforma su propia página de
resultados, con sus propios filtros, a través de yt-dlp, que ya viene con la
app. No se falsea la huella del navegador, no se saltan muros anti-bot, no se
usan proxies y no se guarda nada de nadie. Una búsqueda por clic, la que pide
el usuario y ninguna más. Expoal promete que todo pasa en tu ordenador y eso
sigue siendo verdad: lo único que sale es la palabra que escribes, igual que
cuando pegas un enlace para analizarlo.

EL TRUCO DE LA FECHA: en modo ligero la búsqueda no trae cuándo se publicó cada
vídeo, así que "vistas por día" no se puede calcular. No hace falta: se le pide
a YouTube que filtre por ventana temporal y ordene por visitas, y entonces el
orden que devuelve YA ES la tendencia de esa ventana. Ese filtro viaja en el
parámetro `sp` de la url de resultados, y sus valores están comprobados contra
la web de verdad, no sacados de memoria.
"""
from __future__ import annotations

import urllib.parse

import yt_dlp

# Cada valor es "ordenar por número de visitas" + "publicado en esta ventana".
# Comprobados uno a uno contra youtube.com: con `week` salen los de la semana
# ordenados de más a menos visto, que es exactamente lo que se quiere enseñar.
WINDOWS = {
    "day": "CAMSAggC",
    "week": "CAMSAggD",
    "month": "CAMSAggE",
    "year": "CAMSAggF",
}
DEFAULT_WINDOW = "week"

# Tope de resultados. Alto no sirve de nada (nadie mira más de veinte tendencias)
# y sí cuesta: cuantos más se piden, más tarda y más se carga a la plataforma.
LIMIT = 20
MAX_LIMIT = 50


class TrendsError(RuntimeError):
    """La búsqueda no se pudo completar, con el motivo ya en cristiano."""


def _results_url(query: str, window: str) -> str:
    sp = WINDOWS.get(window) or WINDOWS[DEFAULT_WINDOW]
    return (f"https://www.youtube.com/results"
            f"?search_query={urllib.parse.quote(query)}&sp={sp}")


def _thumbnail(entry: dict) -> str:
    """La miniatura más pequeña que sirva: la lista enseña imágenes diminutas."""
    thumbs = [t for t in (entry.get("thumbnails") or []) if t.get("url")]
    if not thumbs:
        return ""
    con_ancho = [t for t in thumbs if t.get("width")]
    if con_ancho:
        return min(con_ancho, key=lambda t: t["width"])["url"]
    return thumbs[0]["url"]


def _entry(raw: dict) -> dict | None:
    """Deja de cada resultado solo lo que la lista enseña. None si no vale."""
    url = raw.get("url") or ""
    if not url or raw.get("_type") == "playlist":
        return None
    return {
        "id": raw.get("id") or url,
        "title": raw.get("title") or url,
        "url": url,
        "channel": raw.get("channel") or raw.get("uploader") or "",
        "views": raw.get("view_count") or 0,
        "duration": raw.get("duration") or 0,
        "thumbnail": _thumbnail(raw),
    }


def search(query: str, window: str = DEFAULT_WINDOW, limit: int = LIMIT,
           opts: dict | None = None) -> list[dict]:
    """Lo más visto sobre `query` en esa ventana, de más a menos.

    `opts` deja pasar las cookies y las opciones de red de la app, porque una
    búsqueda choca con el mismo anti-bot que una descarga y tiene la misma
    salida: la sesión del navegador del usuario.
    """
    query = (query or "").strip()
    if not query:
        raise TrendsError("Escribe de qué quieres ver las tendencias")
    limit = max(1, min(int(limit or LIMIT), MAX_LIMIT))

    base = {
        "quiet": True,
        "no_warnings": True,
        # En modo ligero: título, canal, visitas y duración de cada uno, sin
        # sondear vídeo por vídeo. Sondearlos serían veinte peticiones más y
        # es justo lo que hace que una plataforma te empiece a decir que no.
        "extract_flat": "in_playlist",
        "playlistend": limit,
    }
    base.update(opts or {})

    try:
        with yt_dlp.YoutubeDL(base) as ydl:
            info = ydl.extract_info(_results_url(query, window), download=False)
    except Exception as exc:  # noqa: BLE001 - se traduce por el mensaje
        raise TrendsError(_clean(exc)) from exc

    entries = [_entry(e) for e in (info.get("entries") or []) if isinstance(e, dict)]
    return [e for e in entries if e][:limit]


def _clean(exc: BaseException) -> str:
    from . import logbus
    msg = logbus.strip_ansi(str(exc)).strip()
    if msg.startswith("ERROR:"):
        msg = msg[len("ERROR:"):].strip()
    return msg or exc.__class__.__name__
