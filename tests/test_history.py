"""Historial en JSON: orden, tope y tolerancia a archivos rotos."""
from __future__ import annotations

import json

from expoal.history import MAX_ENTRIES, History


def test_lo_ultimo_va_primero(tmp_path):
    hist = History(tmp_path / "h.json")
    hist.add({"title": "uno"})
    hist.add({"title": "dos"})
    assert [e["title"] for e in hist.entries()] == ["dos", "uno"]


def test_se_persiste_en_disco(tmp_path):
    ruta = tmp_path / "h.json"
    History(ruta).add({"title": "uno"})
    assert json.loads(ruta.read_text(encoding="utf-8"))[0]["title"] == "uno"
    assert History(ruta).entries()[0]["title"] == "uno"      # y se relee


def test_tope_de_entradas(tmp_path):
    hist = History(tmp_path / "h.json")
    for i in range(MAX_ENTRIES + 10):
        hist.add({"title": str(i)})
    assert len(hist.entries()) == MAX_ENTRIES


def test_un_archivo_roto_no_tumba_la_app(tmp_path):
    ruta = tmp_path / "h.json"
    ruta.write_text("{no es json", encoding="utf-8")
    assert History(ruta).entries() == []


def test_el_bom_de_powershell_rompe_la_lectura(tmp_path):
    """Documenta un fallo real: `Out-File -Encoding utf8` añade BOM y el
    historial se leía vacío (ver FEEDBACK.md, 2026-07-06). El comportamiento
    esperado es no reventar; el archivo se descarta y se empieza de cero."""
    ruta = tmp_path / "h.json"
    ruta.write_bytes(b"\xef\xbb\xbf" + json.dumps([{"title": "uno"}]).encode())
    assert History(ruta).entries() == []


def test_vaciar(tmp_path):
    hist = History(tmp_path / "h.json")
    hist.add({"title": "uno"})
    hist.clear()
    assert hist.entries() == []


def test_los_acentos_se_guardan_legibles(tmp_path):
    ruta = tmp_path / "h.json"
    History(ruta).add({"title": "Canción de Ñu"})
    assert "Canción de Ñu" in ruta.read_text(encoding="utf-8")


def test_la_ultima_carpeta_sale_del_historial(tmp_path):
    # Respaldo para quien ya tenía Expoal antes de que la carpeta se guardara en
    # los ajustes: su historial ya sabe dónde guarda las cosas.
    destino = tmp_path / "Vídeos"
    destino.mkdir()
    h = History(tmp_path / "h.json")
    h.add({"url": "u1", "folder": str(destino)})
    assert h.last_folder() == str(destino)


def test_una_carpeta_del_historial_que_ya_no_existe_se_salta(tmp_path):
    viva = tmp_path / "Viva"
    viva.mkdir()
    h = History(tmp_path / "h.json")
    h.add({"url": "u1", "folder": str(viva)})
    h.add({"url": "u2", "folder": str(tmp_path / "disco-que-no-esta")})
    assert h.last_folder() == str(viva)


def test_sin_historial_no_hay_carpeta(tmp_path):
    assert History(tmp_path / "h.json").last_folder() == ""
