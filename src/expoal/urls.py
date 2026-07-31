"""Limpieza de listas de enlaces pegadas a mano.

Pegar veinte enlaces de golpe es lo normal cuando se han ido guardando en una
nota o en un chat, y lo que se pega nunca viene limpio: líneas en blanco,
comentarios, el mismo vídeo dos veces, un trozo de texto que se coló. Esto lo
ordena ANTES de encolar nada, y dice qué ha descartado en vez de tragárselo en
silencio (que el usuario crea que van 20 y bajen 17 es peor que avisar).
"""
from __future__ import annotations

# Mismo tope que una playlist: por encima de esto la lista de casillas deja de
# ser manejable y la extracción tarda más de lo que nadie espera mirando.
MAX_URLS = 200


def clean_urls(text: str) -> dict:
    """Ordena el texto pegado y devuelve enlaces, descartes y duplicados.

    Se aceptan varios enlaces en la misma línea (pegar de un chat los junta) y
    se ignoran las líneas que empiezan por "#", para poder comentar una lista
    guardada sin tener que borrarla.
    """
    urls: list[str] = []
    seen: set[str] = set()
    invalid = 0
    duplicates = 0
    truncated = False

    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        found = [t for t in line.split() if t.lower().startswith(("http://", "https://"))]
        if not found:
            # Se cuenta la LÍNEA, no cada palabra: decirle a alguien que ha
            # pegado "4 cosas no válidas" porque escribió una frase de cuatro
            # palabras sería absurdo. Y si la línea SÍ trae un enlace, lo demás
            # es la etiqueta que lo acompañaba ("Vídeo 1: https://...") y no se
            # cuenta como error, porque no lo es.
            invalid += 1
            continue
        for token in found:
            if token in seen:
                duplicates += 1
                continue
            if len(urls) >= MAX_URLS:
                truncated = True
                continue
            seen.add(token)
            urls.append(token)

    return {
        "urls": urls,
        "invalid": invalid,
        "duplicates": duplicates,
        "truncated": truncated,
    }
