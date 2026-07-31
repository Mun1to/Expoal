"""Buffer del panel de terminal: cursor, tope y limpieza de la salida."""
from __future__ import annotations

from expoal import logbus


def test_cursor_solo_devuelve_lo_nuevo():
    bus = logbus.LogBus()
    bus.add("uno")
    bus.add("dos")
    first = bus.since(0)
    assert [ln["text"] for ln in first["lines"]] == ["uno", "dos"]

    bus.add("tres")
    second = bus.since(first["cursor"])
    assert [ln["text"] for ln in second["lines"]] == ["tres"]
    assert bus.since(second["cursor"])["lines"] == []


def test_el_tope_descarta_las_viejas_y_avisa():
    bus = logbus.LogBus(capacity=3)
    bus.add("uno")
    cursor = bus.since(0)["cursor"]
    for i in range(5):
        bus.add(f"linea {i}")
    result = bus.since(cursor)
    assert len(result["lines"]) == 3          # solo caben tres
    assert result["lost"] is True             # y se dice que faltan


def test_quita_colores_y_retornos_de_carro():
    bus = logbus.LogBus()
    bus.add("\x1b[0;31mERROR:\x1b[0m algo")
    bus.add("primera version\rversion final")
    textos = [ln["text"] for ln in bus.since(0)["lines"]]
    assert textos == ["ERROR: algo", "version final"]


def test_las_lineas_vacias_no_se_guardan():
    bus = logbus.LogBus()
    bus.add("")
    bus.add("   ")
    bus.add("\x1b[0m")
    assert bus.since(0)["lines"] == []


def test_clear_vacia_pero_el_cursor_sigue_creciendo():
    bus = logbus.LogBus()
    bus.add("uno")
    bus.clear()
    assert bus.since(0)["lines"] == []
    bus.add("dos")
    # El cursor no se reinicia: si se reiniciara, un cliente que iba por 1
    # se perdería la línea nueva por creerla ya vista.
    assert bus.since(0)["lines"][0]["n"] == 2


def test_el_logger_clasifica_los_niveles():
    bus = logbus.LogBus()
    logger = logbus.YtdlpLogger(bus, job="abc")
    logger.debug("[debug] cosas internas")
    logger.debug("[youtube] Extracting URL")   # yt-dlp manda TODO por debug
    logger.warning("cuidado")
    logger.error("se rompió")
    niveles = [(ln["level"], ln["job"]) for ln in bus.since(0)["lines"]]
    assert niveles == [
        ("debug", "abc"), ("info", "abc"), ("warn", "abc"), ("error", "abc"),
    ]


def test_strip_ansi():
    assert logbus.strip_ansi("\x1b[1;33mhola\x1b[0m") == "hola"
    assert logbus.strip_ansi("sin colores") == "sin colores"
