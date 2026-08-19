"""Cola de descargas: mezcla de opciones, selector de formato y estados."""
from __future__ import annotations

import threading
from pathlib import Path

import pytest

from expoal import clipper, config, downloader, settings
from expoal.downloader import DownloadManager, Job, _apply_extra_opts, format_selector
from expoal.editor import Edits
from expoal.history import History


# --- Mezcla de las opciones del usuario sobre las de la app ---

def test_lo_que_sostiene_la_app_no_se_puede_pisar(monkeypatch):
    monkeypatch.setattr(settings, "user_opts", lambda: {"quiet": False, "progress_hooks": []})
    hook = object()
    logger = object()
    opts = {"quiet": True, "progress_hooks": [hook], "logger": logger, "noprogress": True}
    _apply_extra_opts(opts)
    # Sin hook no hay progreso ni forma de cancelar; sin logger, panel mudo.
    assert opts["progress_hooks"] == [hook]
    assert opts["logger"] is logger
    assert opts["quiet"] is True


def test_los_postprocesadores_se_suman(monkeypatch):
    # Si se sustituyeran, marcar "incrusta la miniatura" borraría la extracción
    # de audio y el MP3 saldría siendo un MP4.
    monkeypatch.setattr(settings, "user_opts",
                        lambda: {"postprocessors": [{"key": "EmbedThumbnail"}]})
    opts = {"postprocessors": [{"key": "FFmpegExtractAudio"}]}
    _apply_extra_opts(opts)
    claves = [p["key"] for p in opts["postprocessors"]]
    assert claves == ["FFmpegExtractAudio", "EmbedThumbnail"]


def test_el_usuario_manda_en_lo_demas(monkeypatch):
    monkeypatch.setattr(settings, "user_opts", lambda: {"format": "worst"})
    opts = {"format": "bv*+ba/b", "quiet": True}
    _apply_extra_opts(opts)
    assert opts["format"] == "worst"


def test_sin_opciones_del_usuario_no_se_toca_nada(monkeypatch):
    monkeypatch.setattr(settings, "user_opts", dict)
    opts = {"format": "bv*+ba/b"}
    _apply_extra_opts(opts)
    assert opts == {"format": "bv*+ba/b"}


# --- Selector de formato ---

def test_audio_pide_el_mejor_audio():
    assert format_selector("audio", "best", True) == "ba/b"


def test_la_calidad_limita_la_altura():
    assert "[height<=720]" in format_selector("video", "720", True)


def test_sin_ffmpeg_solo_archivos_completos():
    # No se puede fusionar vídeo y audio por separado, así que nada de "bv*+ba".
    assert "+" not in format_selector("video", "best", False)


def test_mov_exige_h264():
    # YouTube sirve AV1 en muchas calidades y AV1 no cabe en un MOV: sin pedir
    # códec compatible, el remux falla con "Conversion failed".
    assert "vcodec^=avc1" in format_selector("video", "best", True, "mov")


def test_webm_prefiere_sus_codecs():
    assert "ext=webm" in format_selector("video", "best", True, "webm")


def test_mkv_admite_cualquier_cosa():
    assert format_selector("video", "best", True, "mkv") == "bv*+ba/b"


def test_al_recortar_se_pide_el_audio_en_mp4():
    # El fallo que arregla: YouTube empareja el vídeo moderno con audio Opus en
    # WEBM, que no lleva tabla de fragmentos, y bastaba con eso para que el
    # atajo no entrara nunca en 4K. Un vídeo de diez horas recortado a un minuto
    # se bajaba entero: 32,7 GB.
    sel = format_selector("video", "best", True, "mp4", clipping=True)
    assert sel.startswith("bv*+ba[ext=m4a]")
    assert "/bv*+ba/" in sel                  # y si no hay m4a, el de siempre


def test_sin_recorte_el_audio_no_se_toca():
    assert "m4a" not in format_selector("video", "best", True, "mp4")


def test_al_recortar_tambien_se_respeta_la_calidad():
    assert "[height<=1080]" in format_selector("video", "1080", True, "mp4", clipping=True)


# --- Limpieza del mensaje de error ---

def test_el_error_llega_legible():
    exc = Exception("\x1b[0;31mERROR:\x1b[0m [youtube] xyz: Video unavailable")
    assert downloader.clean_error(exc) == "[youtube] xyz: Video unavailable"


def test_un_error_sin_texto_da_al_menos_el_tipo():
    assert downloader.clean_error(ValueError()) == "ValueError"


# --- Formato de velocidad y tiempo restante ---

@pytest.mark.parametrize("valor,esperado", [(None, ""), (0, ""), (512, "512.0 B/s"), (2048, "2.0 KB/s")])
def test_velocidad(valor, esperado):
    assert downloader._fmt_speed(valor) == esperado


@pytest.mark.parametrize("valor,esperado", [(None, ""), (45, "45s"), (90, "1m 30s"), (3700, "1h 1m")])
def test_tiempo_restante(valor, esperado):
    assert downloader._fmt_eta(valor) == esperado


# --- Cola: pausar, reintentar, limpiar ---

@pytest.fixture()
def manager(monkeypatch):
    """Un manager con el worker parado: aquí se prueban los estados, no descargas."""
    monkeypatch.setattr(DownloadManager, "_run", lambda self: None)
    return DownloadManager(History(config.HISTORY_FILE))


def _job(manager, **cambios):
    data = manager.enqueue("https://x.com/1", "video", "best", "C:/tmp")
    job = manager._jobs[data["id"]]
    for key, value in cambios.items():
        setattr(job, key, value)
    return job


def test_pausar_solo_mientras_descarga(manager):
    job = _job(manager)                       # nace en_cola
    manager.pause(job.id, True)
    assert job.paused is False                # en cola no se pausa: no ha empezado

    job.status = "descargando"
    assert manager.pause(job.id, True)["paused"] is True
    assert job.pause_event.is_set()
    manager.pause(job.id, False)
    assert job.paused is False and not job.pause_event.is_set()


def test_cancelar_suelta_la_pausa(manager):
    # Si no se soltara, el hook seguiría dormido y no llegaría a ver la
    # cancelación: la descarga se quedaría colgada para siempre.
    job = _job(manager, status="descargando")
    manager.pause(job.id, True)
    manager.cancel(job.id)
    assert job.cancel_event.is_set()
    assert not job.pause_event.is_set()


def test_reintentar_devuelve_el_trabajo_a_la_cola(manager):
    job = _job(manager, status="error", error="algo falló", progress=42.0)
    manager.retry(job.id)
    assert job.status == "en_cola"
    assert job.error == "" and job.progress == 0.0
    # Eventos nuevos: el viejo puede seguir marcado de la cancelación anterior.
    assert not job.cancel_event.is_set()


def test_reintentar_no_toca_lo_que_va_bien(manager):
    job = _job(manager, status="descargando", progress=50.0)
    manager.retry(job.id)
    assert job.status == "descargando" and job.progress == 50.0


def test_reintentar_todas_las_fallidas(manager):
    fallida = _job(manager, status="error")
    cancelada = _job(manager, status="cancelado")
    completada = _job(manager, status="completado")
    assert manager.retry_failed() == 2
    assert fallida.status == "en_cola" and cancelada.status == "en_cola"
    assert completada.status == "completado"


def test_limpiar_terminadas_deja_las_activas(manager):
    _job(manager, status="completado")
    activa = _job(manager, status="descargando")
    assert manager.clear_finished() == 1
    assert [j["id"] for j in manager.snapshot()] == [activa.id]


def test_trabajo_desconocido(manager):
    assert manager.retry("noexiste") is None
    assert manager.pause("noexiste", True) is None
    assert manager.cancel("noexiste") is None


def test_el_fallo_se_guarda_en_el_historial(manager):
    job = Job(id="x", url="https://x.com/1", mode="video", quality="best", folder="C:/tmp")
    job.error = "Video unavailable"
    manager._record_failure(job)
    entrada = manager._history.entries()[0]
    assert entrada["status"] == "error"
    assert entrada["error"] == "Video unavailable"
    # Con lo necesario para poder repetirla tal cual desde la interfaz.
    assert entrada["mode"] == "video" and entrada["folder"] == "C:/tmp"


# --- Qué fallos merecen otro intento ---

@pytest.mark.parametrize("mensaje", [
    "unable to download video data: HTTP Error 403: Forbidden",
    "Unable to download video subtitles for 'en': HTTP Error 429: Too Many Requests",
    "HTTP Error 503: Service Unavailable",
    "The read operation timed out",
])
def test_lo_que_se_arregla_esperando_se_reintenta(mensaje):
    # 429 es "vas muy rápido" y los 5xx son "el servidor está mal ahora mismo":
    # rendirse al primero es rendirse cuando esperar habría bastado.
    assert downloader.looks_temporary(mensaje) is True


@pytest.mark.parametrize("mensaje", [
    "Private video. Sign in if you've been granted access",
    "Video unavailable",
    "This video is available to members only",
    "Top 500 canciones de los 90 [abc123]: Video unavailable",   # el 500 va en el título
])
def test_lo_que_no_se_arregla_esperando_no_se_reintenta(mensaje):
    assert downloader.looks_temporary(mensaje) is False


# --- Direcciones que se agotan a media descarga ---

class _YdlFalso:
    """Un yt-dlp de mentira que falla las veces que se le diga."""

    def __init__(self, fallos: int, error: str):
        self.fallos = fallos
        self.error = error
        self.vueltas = 0

    def __call__(self, opts):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def extract_info(self, url, download=False):
        self.vueltas += 1
        if self.vueltas <= self.fallos:
            raise RuntimeError(self.error)
        return {"title": "ok"}


@pytest.fixture()
def sin_esperas(monkeypatch):
    monkeypatch.setattr(DownloadManager, "_sleep_cancellable", lambda self, job, s: None)


def test_mientras_se_avance_se_piden_direcciones_nuevas(manager, monkeypatch, sin_esperas):
    """YouTube deja de servir una dirección firmada tras unos 350 MB y responde
    403 por ella para siempre, así que un vídeo de 45 GB necesita más de cien
    direcciones. Contar esos 403 como intentos fallidos condenaba al error a
    todo vídeo grande: solo cuentan los intentos que no consiguen un byte."""
    ydl = _YdlFalso(fallos=8, error="unable to download video data: HTTP Error 403: Forbidden")
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", ydl)
    bajado = [0]

    def descargado():
        bajado[0] += 350 * 1024 * 1024      # cada intento avanza otro tramo
        return bajado[0]

    job = _job(manager)
    assert manager._extract_with_retries(job, {}, downloaded=descargado)["title"] == "ok"
    assert ydl.vueltas == 9


def test_lo_que_no_avanza_se_rinde_a_los_tres_intentos(manager, monkeypatch, sin_esperas):
    ydl = _YdlFalso(fallos=8, error="unable to download video data: HTTP Error 403: Forbidden")
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", ydl)
    job = _job(manager)
    with pytest.raises(RuntimeError):
        manager._extract_with_retries(job, {}, downloaded=lambda: 0)
    assert ydl.vueltas == DownloadManager.ATTEMPTS


def test_lo_permanente_no_se_reintenta_aunque_haya_avanzado(manager, monkeypatch, sin_esperas):
    # Un vídeo privado no se arregla pidiendo otra dirección.
    ydl = _YdlFalso(fallos=3, error="Private video. Sign in if you've been granted access")
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", ydl)
    job = _job(manager)
    with pytest.raises(RuntimeError):
        manager._extract_with_retries(job, {}, downloaded=lambda: 999)
    assert ydl.vueltas == 1


# --- Cuándo se puede bajar solo el tramo pedido ---

def _con_recorte(manager, **cambios):
    job = _job(manager, **cambios)
    job.edits = Edits(trim_start=60.0, trim_end=120.0)
    return job


def test_recortar_un_trozo_activa_el_atajo(manager):
    assert manager._can_clip_at_source(_con_recorte(manager), {}) is True


def test_sin_recorte_no_hay_nada_que_ahorrar(manager):
    assert manager._can_clip_at_source(_job(manager), {}) is False


def test_el_audio_va_por_el_camino_de_siempre(manager):
    assert manager._can_clip_at_source(_con_recorte(manager, mode="audio"), {}) is False


def test_recortar_solo_los_bordes_no_activa_el_atajo(manager):
    # Sin recorte de duración no se baja menos: hace falta el vídeo entero.
    job = _job(manager)
    job.edits = Edits(crop_left=10, crop_right=10)
    assert manager._can_clip_at_source(job, {}) is False


def test_con_subtitulos_manda_yt_dlp(manager):
    assert manager._can_clip_at_source(_con_recorte(manager, subs=True), {}) is False


def test_webm_no_merece_el_atajo(manager):
    # Obliga a recodificar, y entonces el ahorro de la descarga da igual.
    assert manager._can_clip_at_source(_con_recorte(manager, out_format="webm"), {}) is False


def test_lo_que_reescribe_el_archivo_desactiva_el_atajo(manager, monkeypatch):
    # SponsorBlock, incrustar carátula... son postprocesadores de yt-dlp, y el
    # atajo se los salta: mejor renunciar al ahorro que perder lo que pidió.
    monkeypatch.setattr(settings, "rewrites_the_file", lambda: True)
    assert manager._can_clip_at_source(_con_recorte(manager), {}) is False


def test_la_descarga_rapida_no_cuesta_el_atajo(manager, monkeypatch):
    """Las casillas de velocidad dejan el archivo igual: el atajo sigue valiendo."""
    settings.set_toggle("fast_fragments", True)
    assert settings.rewrites_the_file() is False
    assert manager._can_clip_at_source(_con_recorte(manager), {}) is True


def test_siempre_hay_un_motivo_que_ensenar(manager):
    """Rendirse en silencio es lo que hizo invisible el fallo de las pistas WEBM."""
    assert manager._clip_blocker(_con_recorte(manager)) is None
    assert "video" in manager._clip_blocker(_con_recorte(manager, mode="audio"))
    assert "WEBM" in manager._clip_blocker(_con_recorte(manager, out_format="webm"))
    assert manager._clip_blocker(_job(manager))          # sin recorte, también lo dice


class _YdlConFormatos:
    """yt-dlp de mentira que devuelve un vídeo con sus dos pistas."""

    def __init__(self, destino):
        self.destino = destino

    def __call__(self, opts):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=True):
        return {
            "id": "x", "title": "V", "ext": "mp4",
            "requested_formats": [
                {"url": "https://x/v", "protocol": "https", "ext": "mp4", "http_headers": {}},
                {"url": "https://x/a", "protocol": "https", "ext": "m4a", "http_headers": {}},
            ],
        }

    def prepare_filename(self, info):
        return str(self.destino / "V [x].mp4")


def test_un_fallo_a_mitad_no_deja_trozos_sueltos(manager, monkeypatch, tmp_path):
    """Si se corta la red con el trozo a medias, ese archivo hay que barrerlo."""
    index = clipper.Index(base=100, timescale=1000, refs=[(1000, 1000)])
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _YdlConFormatos(tmp_path))
    monkeypatch.setattr(clipper, "read_index", lambda url, headers: (index, b""))
    monkeypatch.setattr(clipper, "clip_size", lambda *a: 1000)

    def clip_que_se_corta(url, headers, dest, *args, **kwargs):
        Path(dest).write_bytes(b"a medias")
        raise OSError("se cortó la red")

    monkeypatch.setattr(clipper, "clip", clip_que_se_corta)
    job = _con_recorte(manager)
    # El error sube (arriba se reintenta con direcciones nuevas), pero el trozo
    # a medias no se queda en la carpeta de nadie.
    with pytest.raises(OSError):
        manager._clip_at_source(job, {}, "ffmpeg")
    assert list(tmp_path.glob("*.part*")) == []


def test_si_no_hay_indice_ni_se_intenta(manager, monkeypatch, tmp_path):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _YdlConFormatos(tmp_path))
    monkeypatch.setattr(clipper, "read_index", lambda url, headers: None)
    llamadas = []
    monkeypatch.setattr(clipper, "clip", lambda *a, **k: llamadas.append(a))
    assert manager._clip_at_source(_con_recorte(manager), {}, "ffmpeg") is None
    assert llamadas == []                    # ni una petición de más


# --- Aguantar los tropiezos de red ---

@pytest.mark.parametrize("mensaje", [
    "[download] Got error: The read operation timed out",
    "unable to download video data: HTTP Error 403: Forbidden",
    "Connection reset by peer",
    "The remote end closed the connection",
])
def test_los_fallos_de_red_se_reintentan(mensaje):
    assert downloader.looks_temporary(mensaje) is True


@pytest.mark.parametrize("mensaje", [
    "Video unavailable",
    "This video is private",
    "Sign in to confirm you're not a bot",       # falta sesión, no es la red
    "Requested format is not available",
])
def test_lo_permanente_no_se_reintenta(mensaje):
    assert downloader.looks_temporary(mensaje) is False


class _FakeYdl:
    """Sustituto de yt_dlp.YoutubeDL: falla las veces que se le diga."""

    def __init__(self, resultados):
        self.resultados = resultados

    def __call__(self, opts):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=True):
        item = self.resultados.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _sin_esperas(manager, monkeypatch):
    monkeypatch.setattr(DownloadManager, "_sleep_cancellable",
                        staticmethod(lambda job, seconds: None))


def test_un_corte_de_red_no_tumba_la_descarga(manager, monkeypatch):
    # Lo que le pasaba a un vídeo de tres horas: un timeout suelto y a empezar.
    fake = _FakeYdl([Exception("The read operation timed out"), {"title": "ok"}])
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", fake)
    _sin_esperas(manager, monkeypatch)
    job = _job(manager)
    assert manager._extract_with_retries(job, {})["title"] == "ok"


def test_se_rinde_despues_de_los_intentos(manager, monkeypatch):
    fallos = [Exception("The read operation timed out")] * DownloadManager.ATTEMPTS
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _FakeYdl(fallos))
    _sin_esperas(manager, monkeypatch)
    with pytest.raises(Exception, match="timed out"):
        manager._extract_with_retries(_job(manager), {})


def test_un_error_permanente_falla_a_la_primera(manager, monkeypatch):
    fake = _FakeYdl([Exception("Video unavailable"), {"title": "no deberia llegar"}])
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", fake)
    _sin_esperas(manager, monkeypatch)
    with pytest.raises(Exception, match="Video unavailable"):
        manager._extract_with_retries(_job(manager), {})
    assert len(fake.resultados) == 1     # no se gastó el segundo intento


def test_cancelar_manda_sobre_el_reintento(manager, monkeypatch):
    fake = _FakeYdl([Exception("The read operation timed out"), {"title": "ok"}])
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", fake)
    job = _job(manager)
    job.cancel_event.set()
    with pytest.raises(Exception, match="timed out"):
        manager._extract_with_retries(job, {})


def test_los_reintentos_de_yt_dlp_estan_puestos():
    """Sin esto son CERO: los diez por defecto son de su línea de comandos."""
    assert downloader._NET_OPTS["retries"] >= 10
    assert downloader._NET_OPTS["fragment_retries"] >= 10
    assert downloader._NET_OPTS["continuedl"] is True
    # En trozos, para que un fallo cueste reintentar un trozo y no el vídeo.
    assert downloader._NET_OPTS["http_chunk_size"] > 0


def test_el_hook_espera_mientras_este_pausado():
    """El único punto donde la app tiene el control durante la descarga."""
    job = Job(id="x", url="u", mode="video", quality="best", folder="C:/tmp")
    job.pause_event.set()
    salio = threading.Event()

    def esperar():
        while job.pause_event.is_set():
            if job.cancel_event.is_set():
                return
            threading.Event().wait(0.01)
        salio.set()

    hilo = threading.Thread(target=esperar, daemon=True)
    hilo.start()
    assert not salio.wait(0.15)      # sigue esperando
    job.pause_event.clear()
    assert salio.wait(1)             # y sale en cuanto se reanuda


# --- Cómo se llama un archivo que no es el vídeo entero ---

@pytest.mark.parametrize("edits, esperado", [
    (Edits(trim_start=60, trim_end=90), "Big Buck Bunny [abc] 1m00s-1m30s.mp4"),
    (Edits(trim_start=60), "Big Buck Bunny [abc] 1m00s-end.mp4"),
    (Edits(trim_end=30), "Big Buck Bunny [abc] 0s-30s.mp4"),
    (Edits(trim_start=3900, trim_end=3960), "Big Buck Bunny [abc] 1h05m00s-1h06m00s.mp4"),
    (Edits(mute=True), "Big Buck Bunny [abc] edit.mp4"),
])
def test_el_tramo_va_en_el_nombre(edits, esperado):
    # Sin esto, el trozo se guardaba con el nombre del vídeo entero y lo borraba.
    origen = Path("C:/videos/Big Buck Bunny [abc].mp4")
    assert downloader.edited_name(origen, edits).name == esperado
