"""Subtítulos: idiomas disponibles y paso a texto limpio."""
from __future__ import annotations

from expoal import subtitles

SRT = """1
00:00:01,000 --> 00:00:04,000
Hola a todos.

2
00:00:04,000 --> 00:00:06,000
Hola a todos.

3
00:00:06,000 --> 00:00:09,000
Esto es una prueba.
"""

VTT = """WEBVTT
Kind: captions
Language: es

00:00:01.000 --> 00:00:04.000 align:start position:0%
<c>Primera</c> línea

00:00:04.000 --> 00:00:06.000
Segunda línea
"""


def test_srt_a_texto_sin_tiempos_ni_repeticiones(tmp_path):
    ruta = tmp_path / "v.srt"
    ruta.write_text(SRT, encoding="utf-8")
    texto = subtitles.to_text(ruta)
    assert "-->" not in texto
    # La frase repetida (los automáticos repiten la anterior en cada cue) va una vez.
    assert texto.count("Hola a todos") == 1
    # Y se separa en líneas por frase, no una por subtítulo.
    assert texto.splitlines() == ["Hola a todos.", "Esto es una prueba."]


def test_vtt_sin_cabeceras_ni_etiquetas(tmp_path):
    ruta = tmp_path / "v.vtt"
    ruta.write_text(VTT, encoding="utf-8")
    texto = subtitles.to_text(ruta)
    assert "WEBVTT" not in texto and "Kind:" not in texto
    assert "<c>" not in texto and "align:start" not in texto
    assert texto == "Primera línea Segunda línea"


def test_idiomas_propios_antes_que_automaticos():
    info = {
        "subtitles": {"es": [{"name": "Español"}]},
        "automatic_captions": {"en": [{"name": "English"}], "fr": [{"name": "Français"}]},
    }
    langs = subtitles.languages(info)
    assert [t["code"] for t in langs] == ["es", "en", "fr"]
    assert langs[0]["automatic"] is False and langs[1]["automatic"] is True


def test_un_idioma_no_se_repite_por_estar_en_los_dos_sitios():
    info = {"subtitles": {"es": [{}]}, "automatic_captions": {"es": [{}]}}
    assert len(subtitles.languages(info)) == 1


def test_video_sin_subtitulos():
    assert subtitles.languages({}) == []
