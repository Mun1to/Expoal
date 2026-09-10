"""La app tiene que poder parecer un navegador de verdad.

Los extractores de TikTok e Instagram piden hacerse pasar por un navegador en
el saludo TLS. Si `curl_cffi` no está, yt-dlp NO falla: avisa por el registro y
pide la página a pelo, así que todo parece funcionar hasta que la plataforma
aprieta y devuelve una página de relleno en vez del vídeo. Es un fallo que se
esconde, y por eso se fija aquí.

El caso que de verdad temo NO es este entorno, es el instalador: PyInstaller no
trae hook para `curl_cffi`, así que un build sin `--collect-all curl_cffi` sale
mudo y roto solo para quien usa el .exe. Estos tests no pueden ver eso (corren
sobre el proyecto, no sobre el .exe), pero sí cazan el otro camino por el que
esto se pierde: que alguien limpie el `pyproject` y se lleve el extra por
delante. Sin red: solo se pregunta qué sabe hacer la librería instalada.

OJO CON `pytest.importorskip` AQUÍ: la primera versión de este archivo lo usaba,
y eso convierte "falta la dependencia" en un test SALTADO, o sea en verde. Es el
mismo antipatrón del checksum del auto-update (FEEDBACK, 2026-08-19): una
comprobación que se desactiva justo cuando encuentra el problema no es una
comprobación. Aquí la falta de `curl_cffi` tiene que salir ROJA.
"""
from __future__ import annotations

import importlib.util

import yt_dlp

FALTA = ("falta curl_cffi: el pyproject tiene que pedir yt-dlp[curl-cffi], y el "
         "build de PyInstaller --collect-all curl_cffi. Sin ello TikTok e "
         "Instagram fallan de forma intermitente y sin decir por qué.")


def test_curl_cffi_esta_instalado():
    # Se mira el buscador de módulos en vez de importar: da el mismo veredicto
    # sin cargar 3 MB de extensión nativa para responder sí o no.
    assert importlib.util.find_spec("curl_cffi") is not None, FALTA


def test_yt_dlp_tiene_huellas_de_navegador():
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        targets = ydl._get_available_impersonate_targets()
    # Medido el 2026-09-10: 37 huellas con curl_cffi 0.15, y 0 sin él. El umbral
    # es 1 a propósito, no 37: lo que importa es que haya alguna, y clavar el
    # número convertiría cada actualización de curl_cffi en un test rojo.
    assert targets, "yt-dlp no encuentra ninguna huella de navegador disponible"


def test_se_puede_pedir_la_huella_que_piden_los_extractores():
    # Que la lista no esté vacía no basta: hay que poder resolver el objetivo
    # que los extractores nombran, y hoy TikTok e Instagram nombran Chrome.
    from yt_dlp.networking.impersonate import ImpersonateTarget

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        disponibles = ydl._get_available_impersonate_targets()
    assert any(ImpersonateTarget("chrome") in t for t, _ in disponibles), (
        "hay huellas, pero ninguna de Chrome: los extractores que la piden por "
        "nombre seguirían cayendo al camino a pelo"
    )
