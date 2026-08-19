"""Reglas del endpoint de descarga que no dependen de la red."""
from __future__ import annotations

import pytest

from expoal import config, settings
from expoal.server import (EditRequest, _folder_for, edits_for, sizes_by_quality,
                           video_heights)


def _pedido(**cambios) -> EditRequest:
    base = dict(trim_start=10.0, trim_end=40.0, crop_top=8, crop_bottom=8,
                crop_left=16, crop_right=16, mute=True)
    base.update(cambios)
    return EditRequest(**base)


def test_en_video_se_respeta_todo():
    edits = edits_for("video", _pedido())
    assert (edits.trim_start, edits.trim_end) == (10.0, 40.0)
    assert edits.has_crop and edits.mute is True


def test_en_audio_solo_se_recorta_la_duracion():
    # Recortar bordes no tiene imagen que recortar, y quitarle el sonido a un
    # sonido deja el archivo vacío.
    edits = edits_for("audio", _pedido())
    assert (edits.trim_start, edits.trim_end) == (10.0, 40.0)
    assert edits.has_crop is False
    assert edits.mute is False
    assert edits.has_trim is True


def test_los_recortes_negativos_se_ignoran():
    edits = edits_for("video", _pedido(crop_top=-50))
    assert edits.crop_top == 0


@pytest.mark.parametrize("modo", ["video", "audio"])
def test_sin_recorte_no_hay_nada_que_hacer(modo):
    edits = edits_for(modo, _pedido(trim_start=None, trim_end=None, crop_top=0,
                                    crop_bottom=0, crop_left=0, crop_right=0,
                                    mute=False))
    assert edits.has_any is False


# --- La carpeta de destino se recuerda ---

def test_la_carpeta_de_la_descarga_queda_guardada(tmp_path):
    destino = tmp_path / "Vídeos"
    destino.mkdir()
    assert _folder_for(str(destino)) == str(destino)
    assert settings.download_folder() == str(destino)


def test_sin_carpeta_pedida_se_usa_la_de_fabrica():
    assert _folder_for("  ") == str(config.DEFAULT_DOWNLOAD_DIR)


# --- Qué calidades se le ofrecen al usuario ---

def test_las_miniaturas_de_youtube_no_son_calidades():
    # Los storyboards (las imágenes de la barra de progreso) llegan mezclados
    # con los formatos, con altura 27/45/90 y sin códec de vídeo. Ofrecerlos
    # como calidad daba "Requested format is not available" sin remedio.
    info = {"formats": [
        {"height": 2160, "vcodec": "av01.0.13M.10"},
        {"height": 1080, "vcodec": "avc1.640028"},
        {"height": 1080, "vcodec": "vp9"},          # repetida: una sola vez
        {"height": None, "vcodec": "none", "acodec": "opus"},   # solo audio
        {"height": 90, "vcodec": "none", "ext": "mhtml"},       # storyboard
        {"height": 45, "vcodec": "none", "ext": "mhtml"},
        {"height": 27, "vcodec": "none", "ext": "mhtml"},
    ]}
    assert video_heights(info) == [2160, 1080]


def test_un_video_sin_formatos_no_ofrece_calidades():
    assert video_heights({}) == []


# --- Lo que va a ocupar cada calidad ---

def _fmt(fid, height, size=0, tbr=0, audio=False):
    """Un formato como los que sirve YouTube: pistas de vídeo y audio sueltas."""
    base = {"format_id": fid, "ext": "m4a" if audio else "mp4", "url": f"https://x/{fid}",
            "protocol": "https", "filesize": size or None, "tbr": tbr or None}
    if audio:
        return {**base, "vcodec": "none", "acodec": "mp4a.40.2", "height": None, "abr": 128}
    return {**base, "vcodec": "avc1.640028", "acodec": "none", "height": height,
            "width": height * 16 // 9}


def _info(*formats, duration=600):
    """GOTCHA: los formatos van de PEOR a MEJOR, como los sirve YouTube.

    yt-dlp se fía de ese orden y da por bueno el último que cumpla el filtro,
    en vez de reordenar por altura. Con la lista al revés elige el peor y el
    peso saldría mal, así que los tests tienen que imitar el orden real.
    """
    return {"duration": duration, "formats": list(formats)}


def test_cada_calidad_dice_lo_que_ocupa():
    # El caso que lo motiva: "mejor calidad" en un vídeo de doce horas son 114 GB
    # y la app no lo decía en ninguna parte.
    info = _info(_fmt("136", 720, size=200_000_000),
                 _fmt("137", 1080, size=500_000_000),
                 _fmt("140", None, size=10_000_000, audio=True))
    sizes = sizes_by_quality(info)
    # El peso incluye la pista de audio, porque es lo que se descarga de verdad.
    assert sizes["1080"] == 510_000_000
    assert sizes["720"] == 210_000_000
    assert sizes["best"] == sizes["1080"]


def test_una_calidad_menor_nunca_pesa_mas():
    info = _info(_fmt("137", 1080, size=500_000_000),
                 _fmt("313", 2160, size=3_000_000_000),
                 _fmt("140", None, size=10_000_000, audio=True))
    sizes = sizes_by_quality(info)
    assert sizes["2160"] > sizes["1080"]


def test_sin_tamano_declarado_se_calcula_con_el_bitrate():
    # YouTube no siempre manda filesize; con el bitrate y la duración sale un
    # número aproximado, que es infinitamente mejor que ninguno.
    info = _info(_fmt("137", 1080, tbr=8000),
                 _fmt("140", None, tbr=128, audio=True), duration=100)
    # 8000 kbit/s durante 100 s = 100 MB, más el audio.
    assert 95_000_000 < sizes_by_quality(info)["1080"] < 110_000_000


def test_un_video_sin_formatos_no_inventa_pesos():
    assert sizes_by_quality({}) == {}


def test_el_peso_nunca_puede_tumbar_el_analisis():
    # Es un extra. Un formato roto se queda sin número, pero el resto sigue.
    info = _info({"format_id": "roto"}, _fmt("137", 1080, size=500_000_000),
                 _fmt("140", None, size=10_000_000, audio=True))
    # El "roto" no tiene ni códecs ni url: yt-dlp lo ignora y sigue.
    assert sizes_by_quality(info)["1080"] == 510_000_000
