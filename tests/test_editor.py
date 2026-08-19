"""Edición con FFmpeg: qué comando se construye y cuándo cuesta caro."""
from __future__ import annotations

from pathlib import Path

import pytest

from expoal.editor import Edits, apply, build_command

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


# --- El trozo no se guarda encima del vídeo entero ---

def _ffmpeg_de_mentira(monkeypatch):
    """Un FFmpeg que no existe pero deja escrito su archivo de salida."""
    import subprocess

    class Resultado:
        returncode = 0
        stderr = ""

    def run(cmd, **kwargs):
        Path(cmd[-1]).write_bytes(b"trozo")
        return Resultado()

    monkeypatch.setattr(subprocess, "run", run)


def test_el_recorte_va_a_otro_archivo_y_el_original_se_queda(tmp_path, monkeypatch):
    # El caso que borraba datos: el vídeo entero ya estaba en la carpeta, se
    # pedía un minuto de él, y el minuto se guardaba con su mismo nombre.
    _ffmpeg_de_mentira(monkeypatch)
    entero = tmp_path / "video.mp4"
    entero.write_bytes(b"el video entero, largo")
    trozo = tmp_path / "video 1m00s-1m30s.mp4"

    salida = apply(entero, Edits(trim_start=60, trim_end=90), "ffmpeg",
                   dest=trozo, keep_source=True)

    assert salida == trozo and trozo.read_bytes() == b"trozo"
    assert entero.exists() and entero.read_bytes() == b"el video entero, largo"


def test_si_lo_bajamos_solo_para_recortarlo_no_se_queda_el_grande(tmp_path, monkeypatch):
    # Al revés: si el vídeo entero se bajó AHORA solo para sacarle el trozo,
    # dejarlo sería regalarle al usuario cuarenta gigas que no pidió.
    _ffmpeg_de_mentira(monkeypatch)
    entero = tmp_path / "video.mp4"
    entero.write_bytes(b"recien bajado")
    trozo = tmp_path / "video 1m00s-1m30s.mp4"

    apply(entero, Edits(trim_start=60, trim_end=90), "ffmpeg", dest=trozo, keep_source=False)

    assert trozo.exists() and not entero.exists()


def test_sin_destino_se_edita_en_el_sitio_como_siempre(tmp_path, monkeypatch):
    _ffmpeg_de_mentira(monkeypatch)
    video = tmp_path / "video.mp4"
    video.write_bytes(b"original")
    assert apply(video, Edits(mute=True), "ffmpeg") == video
    assert video.read_bytes() == b"trozo"
