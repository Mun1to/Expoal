"""El botón que abre la carpeta de un archivo descargado.

Parece una tontería de una línea y es el fallo más fácil de no ver: explorer.exe
no protesta cuando no entiende el argumento, abre Documentos y se queda tan
ancho, así que "no funciona" y "funciona" se parecen mucho desde el código.
"""
from __future__ import annotations

from expoal.dialogs import select_command


def test_select_va_fuera_de_las_comillas():
    # Lo que rompía: subprocess con una lista genera `explorer "/select,C:\...`,
    # con la opción DENTRO de las comillas, y explorer la ignora entera.
    cmd = select_command(r"C:\Videos\mi carpeta\un vídeo [abc123].mp4")
    assert cmd.startswith('explorer /select,"')
    assert not cmd.startswith('explorer "')


def test_la_ruta_va_entrecomillada_entera():
    # Los títulos de vídeo llevan espacios casi siempre: sin comillas, explorer
    # se queda con el primer trozo y no encuentra nada.
    cmd = select_command(r"C:\Videos\mi carpeta\un vídeo [abc123].mp4")
    assert cmd.endswith(r'"C:\Videos\mi carpeta\un vídeo [abc123].mp4"')
