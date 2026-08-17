"""Ajustes: traducción de flags, casillas y cookies.

La parte más delicada de la app: `parse_extra_args` decide qué opciones acaban
en yt-dlp, y un fallo aquí se lleva por delante el formato o la carpeta de
destino sin que nadie se entere hasta ver el archivo en el sitio equivocado.
"""
from __future__ import annotations

import pytest

from expoal import config, settings


# --- Traducción de flags a opciones de la librería ---

def test_texto_vacio_no_cambia_nada():
    assert settings.parse_extra_args("") == {}
    assert settings.parse_extra_args("   ") == {}


def test_solo_devuelve_lo_que_el_usuario_cambio():
    # GOTCHA que motiva el baseline: yt_dlp.parse_options devuelve el diccionario
    # ENTERO con sus cien y pico valores por defecto. Si se aplicara tal cual,
    # pisaría el formato y la plantilla de la app.
    opts = settings.parse_extra_args("--concurrent-fragments 4")
    assert opts == {"concurrent_fragment_downloads": 4}


def test_flags_de_aria2c():
    opts = settings.parse_extra_args(
        '--downloader aria2c --downloader-args "aria2c:-x 16 -s 16 -k 1M"'
    )
    assert opts["external_downloader"] == {"default": "aria2c"}
    assert opts["external_downloader_args"] == {"aria2c": ["-x", "16", "-s", "16", "-k", "1M"]}


def test_sponsorblock_produce_postprocesadores():
    opts = settings.parse_extra_args("--sponsorblock-remove sponsor")
    assert any("SponsorBlock" in p["key"] for p in opts.get("postprocessors", []))


@pytest.mark.parametrize("flag", ["--exec", "--exec-before-download", "--config-location"])
def test_las_opciones_que_ejecutan_programas_estan_bloqueadas(flag):
    # No es desconfiar del usuario: basta con que alguien en un foro le diga
    # "pega esto" para convertir el descargador en una puerta de entrada.
    with pytest.raises(settings.ArgsError):
        settings.parse_extra_args(f'{flag} "echo hola"')


def test_bloqueo_con_igual():
    with pytest.raises(settings.ArgsError):
        settings.parse_extra_args('--exec="echo hola"')


def test_opcion_inexistente_da_mensaje_util():
    with pytest.raises(settings.ArgsError) as exc:
        settings.parse_extra_args("--no-existe-esta-opcion")
    assert "no-existe-esta-opcion" in str(exc.value)


def test_comillas_sin_cerrar():
    with pytest.raises(settings.ArgsError):
        settings.parse_extra_args('--output "sin cerrar')


def test_help_no_vuelca_el_manual():
    # optparse llama a sys.exit con --help y antes escupe el manual entero de
    # yt-dlp; tiene que quedarse en un mensaje corto.
    with pytest.raises(settings.ArgsError) as exc:
        settings.parse_extra_args("--help")
    assert len(str(exc.value)) < 200


def test_no_se_aceptan_enlaces():
    with pytest.raises(settings.ArgsError):
        settings.parse_extra_args("https://youtu.be/xyz")


def test_guardar_valida_antes():
    with pytest.raises(settings.ArgsError):
        settings.set_extra_args("--no-existe")
    assert settings.extra_args() == ""      # y no se guarda nada roto


# --- Casillas ---

def test_toggle_flags_apaga_aria2c_si_no_esta_instalado(monkeypatch):
    monkeypatch.setattr(config, "find_aria2c", lambda: None)
    assert settings.toggle_flags("aria2c") == ""


def test_toggle_flags_usa_la_ruta_real_de_aria2c(monkeypatch):
    monkeypatch.setattr(config, "find_aria2c", lambda: r"C:\bin\aria2c.exe")
    flags = settings.toggle_flags("aria2c")
    assert r"C:\bin\aria2c.exe" in flags
    # Y tiene que seguir siendo traducible por el mismo camino que el resto.
    opts = settings.parse_extra_args(flags)
    assert opts["external_downloader"] == {"default": r"C:\bin\aria2c.exe"}


def test_toggle_flags_apaga_lo_que_necesita_ffmpeg_si_no_esta(monkeypatch):
    monkeypatch.setattr(config, "ffmpeg_available", lambda: False)
    assert settings.toggle_flags("sponsorblock") == ""
    assert settings.toggle_flags("fast_fragments") == "--concurrent-fragments 4"


def test_el_texto_libre_va_despues_de_las_casillas(monkeypatch):
    monkeypatch.setattr(config, "ffmpeg_available", lambda: True)
    settings.set_toggle("embed_metadata", True)
    settings.set_extra_args("--embed-thumbnail")
    linea = settings.user_args_line()
    assert linea.index("--embed-metadata") < linea.index("--embed-thumbnail")


def test_casilla_desconocida():
    with pytest.raises(ValueError):
        settings.set_toggle("no-existe", True)


def test_user_opts_no_revienta_con_ajustes_rotos(monkeypatch):
    # Si una opción guardada deja de existir en una versión nueva de yt-dlp,
    # mejor descargar sin ella que no descargar.
    monkeypatch.setattr(settings, "extra_args", lambda: "--opcion-que-ya-no-existe")
    assert settings.user_opts() == {}


# --- Cookies ---

def test_cookies_del_navegador():
    settings.set_cookies_browser("firefox")
    assert settings.cookie_opts() == {"cookiesfrombrowser": ("firefox",)}


def test_navegador_no_soportado():
    with pytest.raises(ValueError):
        settings.set_cookies_browser("netscape")


def test_archivo_de_cookies(tmp_path):
    galletas = tmp_path / "cookies.txt"
    galletas.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
    settings.set_cookies_file(str(galletas))
    assert settings.cookie_opts() == {"cookiefile": str(galletas)}


def test_archivo_y_navegador_son_excluyentes(tmp_path):
    galletas = tmp_path / "cookies.txt"
    galletas.write_text("x", encoding="utf-8")
    settings.set_cookies_file(str(galletas))
    settings.set_cookies_browser("chrome")
    assert settings.cookies_file() == ""
    settings.set_cookies_file(str(galletas))
    assert settings.cookies_browser() == ""


def test_archivo_inexistente():
    with pytest.raises(ValueError):
        settings.set_cookies_file("C:/no/existe/cookies.txt")


def test_si_el_archivo_desaparece_se_baja_sin_cookies(tmp_path):
    galletas = tmp_path / "cookies.txt"
    galletas.write_text("x", encoding="utf-8")
    settings.set_cookies_file(str(galletas))
    galletas.unlink()
    assert settings.cookie_opts() == {}


# --- Clasificación de errores ---

def test_reconoce_un_fallo_por_falta_de_sesion():
    assert settings.looks_like_login_error("Sign in to confirm you're not a bot")
    assert settings.looks_like_login_error("This video is private")
    assert not settings.looks_like_login_error("Video unavailable")


def test_reconoce_un_fallo_al_leer_las_cookies():
    settings.set_cookies_browser("chrome")
    assert settings.looks_like_cookie_error("Failed to decrypt with DPAPI: cookie database")
    # Un "no such file" que no habla de cookies no cuenta.
    assert not settings.looks_like_cookie_error("No such file or directory: video.mp4")


def test_ajustes_corruptos_vuelven_a_los_valores_por_defecto():
    config.SETTINGS_FILE.write_text("{esto no es json", encoding="utf-8")
    assert settings.load()["cookies_browser"] == ""


# --- Valores nuevos en una instalación que ya existía ---

def test_la_descarga_rapida_viene_puesta():
    # Es de yt-dlp, no necesita nada instalado y no cambia el archivo que sale.
    assert settings.load()["fast_fragments"] is True


def test_un_ajuste_viejo_estrena_la_descarga_rapida():
    # El archivo de quien ya tenía Expoal guarda todas las casillas en false
    # aunque no las haya tocado nunca: sin esto se quedaría sin la mejora.
    settings.save({"fast_fragments": False})
    settings.upgrade_defaults()
    assert settings.load()["fast_fragments"] is True


def test_solo_se_estrena_una_vez():
    settings.upgrade_defaults()
    settings.set_toggle("fast_fragments", False)     # el usuario la desmarca
    settings.upgrade_defaults()
    assert settings.load()["fast_fragments"] is False


def test_se_sabe_como_viene_cada_casilla_de_fabrica():
    # La interfaz lo usa para no abrir el panel de opciones por una casilla que
    # viene marcada de serie: si lo abriera, la pantalla dejaría de nacer simple.
    assert settings.default_of("fast_fragments") is True
    assert settings.default_of("sponsorblock") is False
    assert settings.default_of("no existe") is False


def test_estrenar_no_toca_lo_que_reescribe_el_archivo():
    settings.upgrade_defaults()
    for name in settings.TOGGLES:
        if name not in settings.TOGGLES_SPEED_ONLY:
            assert settings.load()[name] is False


# --- Carpeta de destino recordada ---

def test_sin_carpeta_guardada_no_hay_ninguna():
    assert settings.download_folder() == ""


def test_la_carpeta_sobrevive_al_reinicio(tmp_path):
    destino = tmp_path / "Vídeos"
    destino.mkdir()
    settings.set_download_folder(str(destino))
    # load() vuelve a leer el archivo: es lo mismo que hace el arranque.
    assert settings.download_folder() == str(destino)


def test_una_carpeta_que_ya_no_existe_no_manda(tmp_path):
    # Un disco externo que se quedó fuera no puede dejar la app apuntando a un
    # sitio muerto: se vuelve a la de fábrica.
    settings.set_download_folder(str(tmp_path / "disco-que-no-esta"))
    assert settings.download_folder() == ""
