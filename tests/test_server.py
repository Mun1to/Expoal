"""Reglas del endpoint de descarga que no dependen de la red."""
from __future__ import annotations

import pytest

from expoal import config, settings
from expoal.server import EditRequest, _folder_for, edits_for


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
