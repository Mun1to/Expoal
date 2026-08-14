"""Bajar SOLO el tramo pedido de un vídeo, en vez de bajarlo entero para tirar el 99%.

POR QUÉ EXISTE ESTO: recortar un minuto de un vídeo de tres horas obligaba a
descargar las tres horas y cortarlas después con FFmpeg. Lo obvio sería usar
`--download-sections` de yt-dlp, pero está medido y en YouTube sale PEOR que
bajar el vídeo entero: manda la descarga a FFmpeg, que pide el archivo de una
sentada, y YouTube estrangula esa forma de pedirlo a 0,46 MB/s frente a los
23 MB/s que da pidiéndolo por trozos. Encima FFmpeg tiene que leer desde el
principio para llegar al minuto que sea. Es un problema conocido y abierto en
yt-dlp (issues 6513 y 15036).

CÓMO LO HACE ESTE MÓDULO: los vídeos que sirve YouTube son MP4 fragmentado, y
llevan al principio una tabla (la caja `sidx`) que dice, fragmento a fragmento,
cuántos bytes ocupa y cuánto dura. Leyéndola se sabe SIN ESTIMAR qué bytes
corresponden al minuto que se quiere, y se piden solo esos con cabeceras Range.
Cabecera + esos fragmentos = un vídeo válido que conserva los tiempos
originales, así que el corte fino posterior se pide con los segundos de verdad.

Todo aquí es de vuelta atrás: cualquier cosa que no encaje (sin índice, servidor
que no acepta rangos, otro contenedor) devuelve None y quien llama baja el vídeo
entero como siempre. Nunca peor que antes.
"""
from __future__ import annotations

import struct
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Trozos con los que se piden los bytes. NO es un detalle: pedir un rango enorme
# de una vez vuelve a caer en el estrangulamiento (medido: 78 MB a 0,5 MB/s
# frente a 10 MB a 23 MB/s). El tamaño es el mismo que usa yt-dlp para YouTube.
CHUNK = 10 * 1024 * 1024

# Cuánto se pide para buscar el índice, de menos a más. Se empieza pequeño
# porque en un vídeo normal la tabla está en el primer kilobyte y pedir de más
# es descarga tirada; un vídeo de tres horas con fragmentos de cinco segundos
# tiene unas 2.000 entradas de 12 bytes, y para esos está el escalón siguiente.
HEADER_SIZES = (64 << 10, 1 << 20, 8 << 20)

Progress = Callable[[int, int], None]


@dataclass
class Index:
    """El índice de fragmentos leído de la caja `sidx`."""

    base: int                       # byte donde empieza el primer fragmento
    timescale: int                  # unidades de tiempo por segundo
    refs: list[tuple[int, int]]     # por fragmento: (bytes, duración en unidades)
    start_time: float = 0.0         # segundo en el que empieza el primer fragmento
    # Dónde está la propia tabla dentro de la cabecera. Hace falta para poder
    # QUITARLA del archivo recortado: sus posiciones son las del vídeo completo,
    # y si se deja, quien lo abra buscará el minuto pedido en un byte que ya no
    # existe y no encontrará nada (cazado con un vídeo de prueba: salía un
    # archivo de 262 bytes y cero pistas).
    sidx_pos: int = 0
    sidx_size: int = 0

    @property
    def duration(self) -> float:
        return sum(d for _, d in self.refs) / self.timescale


def _boxes(buf: bytes, pos: int = 0):
    """Recorre las cajas MP4 de nivel superior: (nombre, offset, tamaño)."""
    while pos + 8 <= len(buf):
        size = int.from_bytes(buf[pos:pos + 4], "big")
        name = buf[pos + 4:pos + 8].decode("latin-1", "replace")
        if size == 1:                                   # tamaño de 64 bits
            if pos + 16 > len(buf):
                return
            size = int.from_bytes(buf[pos + 8:pos + 16], "big")
        if size < 8:                                    # 0 = "hasta el final"
            return
        yield name, pos, size
        pos += size


def parse_sidx(header: bytes) -> Index | None:
    """Lee el índice de fragmentos. None si este archivo no lo trae."""
    for name, pos, size in _boxes(header):
        if name != "sidx":
            continue
        if pos + size > len(header):
            return None                                 # está cortado: hace falta más
        p = pos + 8
        version = header[p]
        p += 4 + 4                                      # versión + flags, reference_ID
        (timescale,) = struct.unpack(">I", header[p:p + 4])
        p += 4
        if version == 0:
            earliest, first_offset = struct.unpack(">II", header[p:p + 8])
            p += 8
        else:
            earliest, first_offset = struct.unpack(">QQ", header[p:p + 16])
            p += 16
        p += 2                                          # reservado
        (count,) = struct.unpack(">H", header[p:p + 2])
        p += 2
        if not timescale or not count or p + count * 12 > len(header):
            return None
        refs = []
        for _ in range(count):
            first, duration, _sap = struct.unpack(">III", header[p:p + 12])
            # El bit alto de la primera palabra dice si la referencia apunta a
            # otro sidx en vez de a datos; anidados no los tratamos.
            if first & 0x80000000:
                return None
            refs.append((first & 0x7FFFFFFF, duration))
            p += 12
        return Index(
            base=pos + size + first_offset,
            timescale=timescale,
            refs=refs,
            start_time=earliest / timescale,
            sidx_pos=pos,
            sidx_size=size,
        )
    return None


def header_without_index(header: bytes, index: Index) -> bytes:
    """La cabecera lista para encabezar el trozo, sin la tabla de posiciones.

    Se queda con lo que hace falta para saber leerlo (ftyp, moov) y tira el
    sidx, porque sus posiciones son las del vídeo completo. Sin tabla, quien
    abra el archivo lee los fragmentos en orden, y cada uno lleva dentro el
    segundo en el que va, que es justo lo que queremos conservar.
    """
    return header[:index.sidx_pos] + header[index.sidx_pos + index.sidx_size:index.base]


def self_contained(header: bytes, index: Index) -> bool:
    """¿Se basta cada fragmento a sí mismo, o depende del resto del archivo?

    Lo dice una bandera del primer fragmento (`default-base-is-moof`). Si no la
    lleva, sus posiciones internas se cuentan desde el principio del ARCHIVO
    ENTERO, y un trozo suelto es ilegible: al probarlo con un vídeo así salía un
    archivo de 262 bytes sin una sola imagen. Los vídeos servidos para streaming
    (YouTube entre ellos) sí la llevan, porque es lo que permite empezar a ver
    por la mitad. Se mira sobre el primer fragmento, que ya viene en la cabecera
    descargada, así que no cuesta ni una petición más.
    """
    for name, pos, size in _boxes(header, index.base):
        if name != "moof":
            return False
        end = pos + size
        for tname, tpos, tsize in _boxes(header, pos + 8):
            if tpos >= end:
                break
            if tname != "traf":
                continue
            for fname, fpos, _ in _boxes(header, tpos + 8):
                if fpos >= tpos + tsize:
                    break
                if fname == "tfhd" and fpos + 12 <= len(header):
                    flags = int.from_bytes(header[fpos + 9:fpos + 12], "big")
                    return bool(flags & 0x020000)
        return False
    return False


def byte_range(index: Index, start: float, end: float | None) -> tuple[int, int, float]:
    """Qué bytes hay que pedir para cubrir [start, end], y en qué segundo empiezan.

    Se cogen fragmentos ENTEROS: el que contiene el inicio entra completo, así
    que el archivo empieza un poco antes de lo pedido. Ese sobrante se recorta
    después con FFmpeg, que para eso necesita los tiempos originales intactos.
    """
    t = index.start_time
    offset = index.base
    first_byte: int | None = None
    first_time = t
    for nbytes, ndur in index.refs:
        dur = ndur / index.timescale
        if first_byte is None and t + dur > start:
            first_byte, first_time = offset, t
        if first_byte is not None and end is not None and t >= end:
            return first_byte, offset - 1, first_time
        t += dur
        offset += nbytes
    if first_byte is None:                              # el inicio cae más allá del final
        raise ValueError("El recorte empieza después de que acabe el vídeo")
    return first_byte, offset - 1, first_time


def _request(url: str, headers: dict, first: int, last: int):
    req = urllib.request.Request(url, headers=dict(headers or {}))
    req.add_header("Range", f"bytes={first}-{last}")
    return urllib.request.urlopen(req, timeout=30)


def fetch_range(url: str, headers: dict, first: int, last: int,
                sink=None, progress: Progress | None = None,
                done: int = 0, total: int = 0, retries: int = 3) -> bytes:
    """Descarga [first, last] en trozos, reintentando cada trozo por su cuenta.

    En trozos por dos motivos que van juntos: no volver a caer en el
    estrangulamiento de las peticiones largas, y que un fallo de red cueste
    reintentar diez megas en vez de la descarga entera.
    """
    out = bytearray() if sink is None else None
    pos = first
    while pos <= last:
        stop = min(pos + CHUNK - 1, last)
        for attempt in range(1, retries + 1):
            try:
                with _request(url, headers, pos, stop) as resp:
                    data = resp.read()
                break
            except urllib.error.HTTPError as exc:
                # Un 403 o un 410 aquí significa que la dirección firmada ha
                # caducado, y repetirla da lo mismo por muchas vueltas que se le
                # dé. Se sale para que arriba se pidan direcciones nuevas.
                if exc.code in (403, 410):
                    raise
                if attempt == retries:
                    raise
            except (urllib.error.URLError, OSError, TimeoutError):
                if attempt == retries:
                    raise
        if not data:
            break
        if sink is not None:
            sink.write(data)
        else:
            out.extend(data)
        pos += len(data)
        done += len(data)
        if progress:
            progress(done, total)
    return bytes(out) if out is not None else b""


def read_index(url: str, headers: dict) -> tuple[Index, bytes] | None:
    """Baja la cabecera y saca el índice. None si este vídeo no sirve para esto."""
    for size in HEADER_SIZES:
        try:
            with _request(url, headers, 0, size - 1) as resp:
                # 206 = el servidor entiende de rangos. Un 200 significa que se
                # ha traído el archivo entero y que aquí no hay nada que rascar.
                if resp.status != 206:
                    return None
                header = resp.read()
        except (urllib.error.URLError, OSError, TimeoutError):
            return None
        index = parse_sidx(header)
        if index is not None:
            return index, header
        if len(header) < size:                          # el archivo entero cabía: no hay sidx
            return None
    return None


def clip(url: str, headers: dict, dest: Path, start: float, end: float | None,
         progress: Progress | None = None, done: int = 0, total: int = 0,
         found: tuple[Index, bytes] | None = None) -> float | None:
    """Escribe en `dest` solo el tramo pedido. Devuelve su segundo real de inicio.

    None significa "por aquí no se puede": el vídeo no trae índice o el servidor
    no sirve rangos. Quien llama debe bajarlo entero como siempre. El índice se
    puede pasar ya leído (`found`) para no pedir la cabecera dos veces cuando
    hay que sumar antes lo que va a ocupar todo.
    """
    if found is None:
        found = read_index(url, headers)
    if found is None:
        return None
    index, header = found
    if not self_contained(header, index):
        return None
    try:
        first, last, first_time = byte_range(index, start, end)
    except ValueError:
        return None
    if last < first:
        return None
    with open(dest, "wb") as fh:
        fh.write(header_without_index(header, index))   # sin cabecera no es un vídeo
        fetch_range(url, headers, first, last, sink=fh,
                    progress=progress, done=done, total=total)
    return first_time


def clip_size(index: Index, start: float, end: float | None) -> int:
    """Cuántos bytes va a costar el tramo, para poder pintar el progreso."""
    first, last, _ = byte_range(index, start, end)
    return index.base + max(0, last - first + 1)
