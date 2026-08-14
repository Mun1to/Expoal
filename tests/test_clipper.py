"""Recorte en origen: leer el índice del vídeo y pedir solo los bytes del tramo.

Sin red: se construye un MP4 fragmentado de mentira y se sirve desde un servidor
local que entiende de rangos, que es exactamente lo que hace YouTube.
"""
from __future__ import annotations

import http.server
import struct
import threading
from pathlib import Path

import pytest

from expoal import clipper
from expoal.clipper import Index, byte_range, clip, parse_sidx


# --- Un MP4 fragmentado de juguete ---

def _box(name: str, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + name.encode() + payload


def _sidx(refs: list[tuple[int, int]], timescale: int = 1000,
          earliest: int = 0, first_offset: int = 0) -> bytes:
    payload = struct.pack(">BBBB", 0, 0, 0, 0)          # versión 0 + flags
    payload += struct.pack(">I", 1)                     # reference_ID
    payload += struct.pack(">I", timescale)
    payload += struct.pack(">II", earliest, first_offset)
    payload += struct.pack(">HH", 0, len(refs))
    for nbytes, dur in refs:
        payload += struct.pack(">III", nbytes, dur, 0)
    return _box("sidx", payload)


def _fragment(nbytes: int, relleno: bytes, suelto: bool = False) -> bytes:
    """Un fragmento como los de verdad: moof (con su tfhd) y detrás los datos.

    `suelto` = sin la bandera default-base-is-moof, o sea, uno de esos vídeos
    cuyos fragmentos dependen del archivo entero y no se pueden recortar.
    """
    flags = 0 if suelto else 0x020000
    tfhd = _box("tfhd", struct.pack(">II", flags, 1))    # versión 0 + flags, track
    moof = _box("moof", _box("mfhd", b"\0" * 8) + _box("traf", tfhd))
    return moof + _box("mdat", relleno * (nbytes - len(moof) - 8))


def _fake_video(refs: list[tuple[int, int]], timescale: int = 1000,
                suelto: bool = False) -> bytes:
    """Cabecera (ftyp + sidx) y detrás los fragmentos, del tamaño que declaran."""
    header = _box("ftyp", b"isom" * 4) + _sidx(refs, timescale)
    # Cada fragmento se rellena con una letra distinta para reconocerlos.
    body = b"".join(_fragment(nbytes, bytes([65 + i % 26]), suelto)
                    for i, (nbytes, _) in enumerate(refs))
    return header + body


REFS = [(1000, 2000)] * 10          # 10 fragmentos de 1000 bytes y 2 segundos


# --- Leer el índice ---

def test_el_indice_sale_del_propio_video():
    index = parse_sidx(_fake_video(REFS))
    assert index is not None
    assert len(index.refs) == 10
    assert index.timescale == 1000
    assert index.duration == 20.0
    # El primer fragmento empieza justo después de ftyp + sidx.
    assert index.base == len(_box("ftyp", b"isom" * 4)) + len(_sidx(REFS))


def test_un_archivo_sin_indice_no_sirve():
    # Un MP4 normal (no fragmentado) no trae sidx: hay que bajarlo entero.
    assert parse_sidx(_box("ftyp", b"isom") + _box("moov", b"x" * 100)) is None


def test_un_indice_cortado_no_se_inventa():
    """Si la cabecera pedida se quedó corta, mejor None que datos a medias."""
    entero = _fake_video(REFS)
    dentro_del_indice = len(_box("ftyp", b"isom" * 4)) + 40
    assert parse_sidx(entero[:dentro_del_indice]) is None


def test_el_tiempo_de_arranque_se_respeta():
    # earliest_presentation_time distinto de cero: el vídeo no empieza en 0.
    header = _box("ftyp", b"isom") + _sidx(REFS, earliest=5000)
    index = parse_sidx(header)
    assert index.start_time == 5.0


# --- Elegir el tramo ---

@pytest.fixture()
def index():
    return parse_sidx(_fake_video(REFS))


def test_el_tramo_pedido_se_traduce_a_bytes(index):
    # Del segundo 4 al 8: fragmentos 3.º y 4.º (empiezan en 4 y 6).
    first, last, first_time = byte_range(index, 4.0, 8.0)
    assert first == index.base + 2000        # se saltan dos fragmentos de 1000
    assert last == index.base + 4000 - 1
    assert first_time == 4.0


def test_el_fragmento_que_contiene_el_inicio_entra_entero(index):
    # Pidiendo desde el segundo 5 (mitad del tercer fragmento) el archivo tiene
    # que empezar en el 4: el sobrante lo recorta FFmpeg después.
    first, _last, first_time = byte_range(index, 5.0, 9.0)
    assert first == index.base + 2000
    assert first_time == 4.0


def test_sin_final_se_coge_hasta_el_ultimo(index):
    first, last, _ = byte_range(index, 16.0, None)
    assert first == index.base + 8000
    assert last == index.base + 10000 - 1


def test_un_recorte_fuera_del_video_se_rechaza(index):
    with pytest.raises(ValueError):
        byte_range(index, 999.0, None)


def test_se_sabe_lo_que_va_a_costar(index):
    # Cabecera + dos fragmentos, que es lo que se pinta en la barra de progreso.
    assert clipper.clip_size(index, 4.0, 8.0) == index.base + 2000


# --- Descarga real contra un servidor local que entiende de rangos ---

class _Handler(http.server.BaseHTTPRequestHandler):
    data = b""
    ranges_ok = True

    def do_GET(self):                                    # noqa: N802 (lo pide la clase base)
        rango = self.headers.get("Range")
        if not rango or not self.ranges_ok:
            self.send_response(200)
            self.send_header("Content-Length", str(len(self.data)))
            self.end_headers()
            self.wfile.write(self.data)
            return
        first, last = rango.removeprefix("bytes=").split("-")
        first = int(first)
        last = min(int(last), len(self.data) - 1)
        trozo = self.data[first:last + 1]
        self.send_response(206)
        self.send_header("Content-Range", f"bytes {first}-{last}/{len(self.data)}")
        self.send_header("Content-Length", str(len(trozo)))
        self.end_headers()
        self.wfile.write(trozo)

    def log_message(self, *args):
        pass                                             # sin ruido en la salida


@pytest.fixture()
def servidor():
    def arrancar(data: bytes, ranges_ok: bool = True) -> str:
        _Handler.data = data
        _Handler.ranges_ok = ranges_ok
        httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        arrancar.servidores.append(httpd)
        return f"http://127.0.0.1:{httpd.server_address[1]}/v.mp4"
    arrancar.servidores = []
    yield arrancar
    for httpd in arrancar.servidores:
        httpd.shutdown()


def test_solo_se_baja_el_tramo(servidor, tmp_path: Path):
    video = _fake_video(REFS)
    url = servidor(video)
    dest = tmp_path / "trozo.mp4"
    inicio = clip(url, {}, dest, 4.0, 8.0)

    assert inicio == 4.0
    escrito = dest.read_bytes()
    index = parse_sidx(video)
    cabecera = clipper.header_without_index(video, index)
    # Cabecera + los dos fragmentos del tramo, y NADA del resto del vídeo.
    assert len(escrito) == len(cabecera) + 2000
    assert escrito[:len(cabecera)] == cabecera
    assert escrito[len(cabecera):] == video[index.base + 2000:index.base + 4000]
    assert b"A" not in escrito and b"E" not in escrito    # ni el antes ni el después
    assert len(escrito) < len(video) / 2


def test_la_tabla_de_posiciones_no_viaja_con_el_trozo(servidor, tmp_path: Path):
    """Sus posiciones son las del vídeo entero: dejarla deja el trozo ilegible.

    Cazado con un vídeo de verdad: FFmpeg buscaba el minuto pedido en un byte
    que ya no existía y devolvía un archivo de 262 bytes sin una sola imagen.
    """
    video = _fake_video(REFS)
    dest = tmp_path / "trozo.mp4"
    clip(servidor(video), {}, dest, 4.0, 8.0)
    escrito = dest.read_bytes()
    assert b"sidx" not in escrito
    assert escrito.startswith(_box("ftyp", b"isom" * 4))    # lo que sí hace falta


def test_se_avisa_del_progreso(servidor, tmp_path: Path):
    url = servidor(_fake_video(REFS))
    vistos = []
    clip(url, {}, tmp_path / "t.mp4", 0.0, 20.0,
         progress=lambda done, total: vistos.append(done), total=10000)
    assert vistos and vistos[-1] == 10000


def test_cancelar_corta_la_descarga_al_momento(servidor, tmp_path: Path):
    """Así es como se cancela: el aviso de progreso lanza y nadie lo tapa."""
    class Cancelado(Exception):
        pass

    def progress(done, total):
        raise Cancelado()

    with pytest.raises(Cancelado):
        clip(servidor(_fake_video(REFS)), {}, tmp_path / "t.mp4", 0.0, 20.0,
             progress=progress)


def test_un_servidor_sin_rangos_manda_bajarlo_entero(servidor, tmp_path: Path):
    # Devuelve None en vez de intentarlo: quien llama usa el camino de siempre.
    url = servidor(_fake_video(REFS), ranges_ok=False)
    assert clip(url, {}, tmp_path / "t.mp4", 4.0, 8.0) is None


def test_un_video_sin_indice_manda_bajarlo_entero(servidor, tmp_path: Path):
    url = servidor(_box("ftyp", b"isom") + b"x" * 5000)
    assert clip(url, {}, tmp_path / "t.mp4", 4.0, 8.0) is None


def test_los_fragmentos_que_dependen_del_archivo_entero_no_se_recortan(servidor,
                                                                       tmp_path: Path):
    """Sin default-base-is-moof, un trozo suelto sale ilegible: mejor no tocarlo.

    Cazado con un vídeo de prueba real: el recorte devolvía 262 bytes y cero
    imágenes. Ahora se detecta antes de bajar nada y se usa el camino normal.
    """
    url = servidor(_fake_video(REFS, suelto=True))
    assert clip(url, {}, tmp_path / "t.mp4", 4.0, 8.0) is None


def test_los_fragmentos_normales_si_se_recortan():
    video = _fake_video(REFS)
    assert clipper.self_contained(video, parse_sidx(video)) is True
    suelto = _fake_video(REFS, suelto=True)
    assert clipper.self_contained(suelto, parse_sidx(suelto)) is False


def test_los_trozos_grandes_se_piden_de_diez_en_diez_megas(servidor, tmp_path: Path,
                                                           monkeypatch):
    """Pedir un rango enorme de una vez vuelve a caer en el estrangulamiento."""
    peticiones = []
    original = clipper._request

    def espia(url, headers, first, last):
        peticiones.append((first, last))
        return original(url, headers, first, last)

    monkeypatch.setattr(clipper, "_request", espia)
    monkeypatch.setattr(clipper, "CHUNK", 4096)
    url = servidor(_fake_video(REFS))
    clip(url, {}, tmp_path / "t.mp4", 0.0, 20.0)
    # La cabecera va aparte; el cuerpo (10.000 bytes) en trozos de 4 KB.
    del peticiones[0]
    assert len(peticiones) == 3
    assert all(last - first + 1 <= 4096 for first, last in peticiones)
