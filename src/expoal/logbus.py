"""Registro en vivo de lo que hace el motor por detrás.

POR QUÉ: cuando una descarga falla o tarda, la interfaz solo puede decir
"Error" o "Descargando...". Eso basta para el 95% de los casos, pero cuando algo
va mal el usuario (o quien le ayuda) necesita ver lo que ve la línea de comandos:
qué extractor entró, qué formato eligió, si está fusionando, qué dijo yt-dlp
exactamente. Este módulo guarda esas líneas en memoria y la interfaz las pinta en
un panel plegable con pinta de terminal.

En memoria y con tope a propósito: es una ventana a lo que está pasando ahora
mismo, no un archivo de registro que crece en el disco de nadie. Si hiciera falta
guardarlo, el usuario copia y pega lo que ve.
"""
from __future__ import annotations

import re
import threading
import time
from collections import deque

# Cuántas líneas se conservan. Una descarga normal genera unas 15; con 400 caben
# muchas descargas seguidas y el consumo de memoria es despreciable.
CAPACITY = 400

# yt-dlp colorea su salida y usa retornos de carro para redibujar la línea de
# progreso. En un panel HTML eso son caracteres basura, así que se limpian.
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    """Quita los códigos de color. yt-dlp los mete cuando cree que hay terminal.

    Lo usa también el mensaje de error de los trabajos: sin esto, en la interfaz
    y en el historial se leería "ESC[0;31mERROR:ESC[0m Video unavailable".
    """
    return _ANSI.sub("", str(text))


def _clean(text: str) -> str:
    text = strip_ansi(text)
    # El retorno de carro reescribe la línea en una terminal; aquí nos quedamos
    # con el último trozo, que es el estado más reciente.
    if "\r" in text:
        text = text.split("\r")[-1]
    return text.strip()


class LogBus:
    """Buffer circular de líneas, leído por sondeo con un cursor incremental.

    El cursor es un número de línea que solo crece: el cliente pide "lo que haya
    después de N" y recibe eso y el N nuevo. Así no hay que mandar el buffer
    entero en cada sondeo ni preocuparse de que se repitan líneas.
    """

    def __init__(self, capacity: int = CAPACITY):
        self._lines: deque[dict] = deque(maxlen=capacity)
        self._lock = threading.Lock()
        self._seq = 0

    def add(self, text: str, level: str = "info", job: str = "") -> None:
        text = _clean(text)
        if not text:
            return
        with self._lock:
            self._seq += 1
            self._lines.append(
                {
                    "n": self._seq,
                    "at": time.strftime("%H:%M:%S"),
                    "level": level,
                    "job": job,
                    "text": text,
                }
            )

    def since(self, after: int = 0) -> dict:
        """Las líneas posteriores al cursor dado, más el cursor nuevo.

        `lost` avisa de que el buffer dio la vuelta y se perdieron líneas que el
        cliente no llegó a leer: mejor decirlo que fingir que no faltó nada.
        """
        with self._lock:
            lines = [ln for ln in self._lines if ln["n"] > after]
            oldest = self._lines[0]["n"] if self._lines else self._seq + 1
            lost = after > 0 and oldest > after + 1
            return {"lines": lines, "cursor": self._seq, "lost": lost}

    def clear(self) -> None:
        with self._lock:
            self._lines.clear()


class YtdlpLogger:
    """Adaptador que le pasa a yt-dlp lo que espera: debug/info/warning/error.

    GOTCHA: yt-dlp manda TODO por `debug()` (mira `YoutubeDL.to_screen`), y sus
    mensajes de depuración de verdad son los que empiezan por "[debug]". Por eso
    se reclasifica aquí, o el panel saldría entero en gris.

    Otro detalle importante: en cuanto hay un `logger`, yt-dlp ignora `quiet` y
    manda igualmente los mensajes. Es justo lo que queremos —la app sigue callada
    en la consola y el panel recibe todo— pero conviene saberlo antes de tocar
    esas opciones.
    """

    def __init__(self, bus: LogBus, job: str = ""):
        self._bus = bus
        self._job = job

    def debug(self, msg: str) -> None:
        text = str(msg)
        self._bus.add(text, "debug" if text.startswith("[debug]") else "info", self._job)

    def info(self, msg: str) -> None:
        self._bus.add(msg, "info", self._job)

    def warning(self, msg: str) -> None:
        self._bus.add(msg, "warn", self._job)

    def error(self, msg: str) -> None:
        self._bus.add(msg, "error", self._job)


# Único para toda la app: la interfaz enseña un panel, no uno por descarga.
bus = LogBus()
