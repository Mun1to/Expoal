"""Limpieza de listas de enlaces pegadas a mano."""
from __future__ import annotations

from expoal import urls


def test_quita_duplicados_y_conserva_el_orden():
    result = urls.clean_urls(
        "https://a.com/1\nhttps://b.com/2\nhttps://a.com/1\nhttps://c.com/3"
    )
    assert result["urls"] == ["https://a.com/1", "https://b.com/2", "https://c.com/3"]
    assert result["duplicates"] == 1


def test_varios_enlaces_en_la_misma_linea():
    result = urls.clean_urls("https://a.com/1   https://b.com/2")
    assert result["urls"] == ["https://a.com/1", "https://b.com/2"]


def test_ignora_comentarios_y_lineas_vacias():
    result = urls.clean_urls("# mi lista\n\nhttps://a.com/1\n\n#otro comentario")
    assert result["urls"] == ["https://a.com/1"]
    assert result["invalid"] == 0


def test_una_linea_sin_enlace_cuenta_una_vez():
    # Y no una por palabra: decir "4 no válidos" por una frase de 4 palabras
    # sería absurdo para quien lo lee.
    result = urls.clean_urls("esto no es un enlace")
    assert result["urls"] == []
    assert result["invalid"] == 1


def test_el_texto_que_acompana_a_un_enlace_no_es_un_error():
    result = urls.clean_urls("Vídeo 1: https://a.com/1")
    assert result["urls"] == ["https://a.com/1"]
    assert result["invalid"] == 0


def test_solo_http_y_https():
    result = urls.clean_urls("ftp://a.com/1\nfile:///C:/x.mp4\nhttps://b.com/2")
    assert result["urls"] == ["https://b.com/2"]
    assert result["invalid"] == 2


def test_tope_de_enlaces():
    muchos = "\n".join(f"https://a.com/{i}" for i in range(urls.MAX_URLS + 5))
    result = urls.clean_urls(muchos)
    assert len(result["urls"]) == urls.MAX_URLS
    assert result["truncated"] is True


def test_texto_vacio():
    assert urls.clean_urls("")["urls"] == []
    assert urls.clean_urls(None)["urls"] == []
