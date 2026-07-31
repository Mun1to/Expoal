"""Edición con FFmpeg: qué comando se construye y cuándo cuesta caro."""
from __future__ import annotations

from pathlib import Path

import pytest

from expoal.editor import Edits, build_command

SRC = Path("entrada.mp4")
DST = Path("salida.mp4")


def cmd(edits, **kwargs):
    return build_command(SRC, DST, edits, "ffmpeg", **kwargs)


def test_sin_recorte_de_bordes_se_copian_los_flujos():
    # La regla de coste del módulo: copiar es instantáneo, recodificar no.
    orden = cmd(Edits(trim_start=5, trim_end=10))
    assert "-c:v" in orden and orden[orden.index("-c:v") + 1] == "copy"
    assert "libx264" not in orden


def test_recortar_bordes_obliga_a_recodificar():
    orden = cmd(Edits(crop_top=10), width=1920, height=1080)
    assert "libx264" in orden
    assert "crop=1920:1070:0:10" in orden


def test_el_recorte_fuerza_dimensiones_pares():
    # H.264 lo exige: con un lado impar, FFmpeg falla.
    orden = cmd(Edits(crop_top=5), width=1920, height=1080)
    assert "crop=1920:1074:0:5" in orden


def test_un_recorte_imposible_se_rechaza():
    with pytest.raises(ValueError):
        cmd(Edits(crop_left=1000, crop_right=1000), width=1920, height=1080)


def test_recortar_sin_saber_el_tamano_del_video():
    with pytest.raises(ValueError):
        cmd(Edits(crop_top=10))


def test_silenciar():
    assert "-an" in cmd(Edits(mute=True))


def test_el_corte_empieza_en_cero():
    orden = cmd(Edits(trim_start=3, trim_end=8))
    assert "-avoid_negative_ts" in orden
    # -ss antes de -i (búsqueda rápida) y la duración calculada, no el instante final.
    assert orden.index("-ss") < orden.index("-i")
    assert orden[orden.index("-t") + 1] == "5.000"


def test_sin_ediciones_no_hay_nada_que_hacer():
    assert Edits().has_any is False
