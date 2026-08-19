"""Tendencias: buscar qué se mueve en un tema, sin red y sin sondear vídeos.

Lo que se prueba aquí es lo que decide si la lista sale bien o miente: la url
que se pide (el filtro va dentro), qué se conserva de cada resultado y que
ninguna entrada rara tumbe la búsqueda entera.
"""
from __future__ import annotations

import pytest

from expoal import trends


# --- La url que se pide, que es donde vive el filtro ---

def test_la_ventana_viaja_en_la_url():
    url = trends._results_url("gatos", "week")
    assert "search_query=gatos" in url
    assert f"sp={trends.WINDOWS['week']}" in url


def test_cada_ventana_pide_un_filtro_distinto():
    vistos = {trends.WINDOWS[w] for w in trends.WINDOWS}
    assert len(vistos) == len(trends.WINDOWS)


def test_una_ventana_inventada_no_revienta():
    # La manda el navegador: no puede tumbar nada, se cae a la de por defecto.
    assert trends.WINDOWS[trends.DEFAULT_WINDOW] in trends._results_url("x", "el mes pasado")


def test_la_busqueda_se_escapa():
    # Sin escapar, un "&" partiría la url y la búsqueda sería otra.
    url = trends._results_url("rock & roll", "day")
    assert "rock%20%26%20roll" in url or "rock+%26+roll" in url
    assert url.count("&") == 1          # solo el que separa sp=


# --- Qué se conserva de cada resultado ---

def _crudo(**cambios):
    base = {"id": "abc", "title": "Un vídeo", "url": "https://youtu.be/abc",
            "channel": "Canal", "view_count": 1234, "duration": 90,
            "thumbnails": [{"url": "https://i/g.jpg", "width": 480},
                           {"url": "https://i/p.jpg", "width": 120}]}
    base.update(cambios)
    return base


def test_de_cada_resultado_se_guarda_lo_que_se_ensena():
    e = trends._entry(_crudo())
    assert e["title"] == "Un vídeo" and e["channel"] == "Canal"
    assert e["views"] == 1234 and e["duration"] == 90


def test_se_coge_la_miniatura_mas_pequena():
    # La lista las enseña diminutas: bajar la grande es tirar ancho de banda.
    assert trends._entry(_crudo())["thumbnail"] == "https://i/p.jpg"


def test_sin_miniatura_no_falla():
    assert trends._entry(_crudo(thumbnails=[]))["thumbnail"] == ""


def test_un_resultado_sin_enlace_se_descarta():
    assert trends._entry(_crudo(url="")) is None


def test_una_lista_dentro_de_los_resultados_se_descarta():
    # Buscar devuelve a veces listas de reproducción; aquí solo van vídeos.
    assert trends._entry(_crudo(_type="playlist")) is None


def test_un_resultado_sin_titulo_ensena_su_enlace():
    assert trends._entry(_crudo(title=None))["title"] == "https://youtu.be/abc"


# --- La búsqueda entera, con yt-dlp de mentira ---

class _YdlFalso:
    ultimo_url = None
    ultimas_opts = None

    def __init__(self, opts):
        _YdlFalso.ultimas_opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def extract_info(self, url, download=False):
        _YdlFalso.ultimo_url = url
        return {"entries": [_crudo(id=str(i), title=f"V{i}") for i in range(30)]}


@pytest.fixture()
def ydl(monkeypatch):
    monkeypatch.setattr(trends.yt_dlp, "YoutubeDL", _YdlFalso)
    return _YdlFalso


def test_no_se_devuelven_mas_de_los_pedidos(ydl):
    assert len(trends.search("ia", limit=5)) == 5


def test_el_tope_protege_de_una_peticion_absurda(ydl):
    assert len(trends.search("ia", limit=9999)) <= trends.MAX_LIMIT


def test_no_se_sondea_video_por_video(ydl):
    # Sondearlos serían veinte peticiones más, y eso es lo que dispara el
    # anti-bot de la plataforma.
    trends.search("ia")
    assert ydl.ultimas_opts["extract_flat"] == "in_playlist"


def test_las_cookies_del_usuario_llegan_a_la_busqueda(ydl):
    # Una búsqueda topa con el mismo anti-bot que una descarga.
    trends.search("ia", opts={"cookiesfrombrowser": ("firefox",)})
    assert ydl.ultimas_opts["cookiesfrombrowser"] == ("firefox",)


def test_una_busqueda_vacia_se_rechaza_antes_de_pedir_nada(ydl):
    ydl.ultimo_url = None
    with pytest.raises(trends.TrendsError):
        trends.search("   ")
    assert ydl.ultimo_url is None


def test_un_fallo_de_red_llega_legible(monkeypatch):
    class Revienta(_YdlFalso):
        def extract_info(self, url, download=False):
            raise Exception("\x1b[0;31mERROR:\x1b[0m Sign in to confirm you're not a bot")
    monkeypatch.setattr(trends.yt_dlp, "YoutubeDL", Revienta)
    with pytest.raises(trends.TrendsError) as exc:
        trends.search("ia")
    assert str(exc.value) == "Sign in to confirm you're not a bot"
