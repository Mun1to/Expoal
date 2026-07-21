# FEEDBACK.md — Memoria viva de Expoal

Registro de obstáculos técnicos, causas raíz y soluciones exactas.
Leer SIEMPRE antes de empezar una tarea en este proyecto.

---

## 2026-07-06 — FFmpeg instalado con winget no aparece en el PATH de procesos ya abiertos

- **Problema:** tras `winget install Gyan.FFmpeg`, `shutil.which("ffmpeg")` devolvía `None`
  en la sesión activa (el PATH de usuario actualizado solo lo ven procesos nuevos).
- **Causa raíz:** winget modifica el PATH de usuario en el registro, pero los procesos en
  ejecución conservan su copia del entorno.
- **Solución:** `config.find_ffmpeg()` busca primero en el PATH y, si no está, hace glob en
  `%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\**\bin\ffmpeg.exe` y pasa la ruta a
  yt-dlp vía `ffmpeg_location`. Así funciona sin reiniciar la terminal.

## 2026-07-06 — El cambio de tema no re-resolvía las variables CSS en los descendientes

- **Problema:** al pulsar el toggle, `data-theme` cambiaba y las `--var` del `:root` se
  actualizaban, pero `getComputedStyle(document.body).backgroundColor` seguía con el color
  viejo hasta recargar la página. El tema solo "pegaba" tras un F5.
- **Causa raíz:** el motor del preview (Chromium embebido) no re-resolvía en algunos casos los
  `var()` heredados al cambiar solo el atributo del `<html>`; faltaba invalidar el estilo.
- **Solución:** tras cambiar `data-theme`, forzar un reflow síncrono en JS
  (`body.style.display='none'; void body.offsetHeight; body.style.display=''`). Además se separó
  `background-color`/`background-image` en vez del atajo `background` para que la variable de
  color se recalcule limpia. Con esto el toggle es instantáneo y sin recarga.

## 2026-07-06 — Expoal.exe (PyInstaller --windowed) no arrancaba el servidor web

- **Problema 1:** con `--windowed`, `print()` en el arranque lanzaba `AttributeError` porque
  `sys.stdout` es `None` en apps sin consola → el servidor moría antes de escuchar.
  **Solución:** `if sys.stdout is not None: print(...)`.
- **Problema 2 (falsa alarma):** el primer arranque del .exe recién compilado parecía no
  responder. **Causa:** Windows Defender escanea el binario nuevo en su primera ejecución y
  añade varios segundos de retraso. En el segundo intento respondía normal. No es un bug del
  código; dar margen (o excluir la carpeta dist en Defender) al probar builds frescas.
- **Nota:** `uvicorn.run(app, ...)` con el objeto app importado directamente (no el string
  `"expoal.server:app"`) es necesario para que PyInstaller congele el módulo en el .exe.

## 2026-07-06 — El historial no cargaba en las capturas (BOM de PowerShell)

- **Problema:** al preparar el historial de ejemplo para las capturas escribiéndolo con
  `Out-File -Encoding utf8` (PowerShell 5.1), la app lo leía como vacío y las capturas salían
  sin la sección de historial.
- **Causa raíz:** `Out-File -Encoding utf8` en Windows PowerShell 5.1 añade un BOM al inicio.
  `history.py` hace `json.loads(path.read_text(encoding="utf-8"))`, que NO descarta el BOM, así
  que `json.loads` falla y el `except` devuelve `[]` (historial vacío).
- **Solución:** escribir el JSON SIN BOM (con la herramienta Write, o
  `[System.IO.File]::WriteAllText` con `UTF8Encoding($false)`). Aprendizaje: nunca generar con
  `Out-File -Encoding utf8` archivos que va a parsear otra herramienta.

## 2026-07-20 — El auto-update cerraba la app pero NO actualizaba (AppMutex)

- **Síntoma:** pulsar "Actualizar" cerraba Expoal y no pasaba nada más: ni se instalaba la
  versión nueva ni se reabría la app. La descarga sí funcionaba (el .exe aparecía en `%TEMP%`).
- **Diagnóstico:** ejecutar el instalador a mano con `/LOG` reprodujo el fallo (exit code **1**).
  El log lo decía literal:
  `Defaulting to Cancel for suppressed message box: "...ha detectado que Expoal está
  ejecutándose. Por favor, ciérrelo ahora..."` → `Got EAbort exception`.
- **Causa raíz:** el `AppMutex=ExpoalRunningMutex` del .iss. Con AppMutex, Setup detecta la app
  viva y muestra un cuadro "ciérrela y pulse Aceptar"; en modo `/SILENT /SUPPRESSMSGBOXES` ese
  cuadro se auto-responde **Cancelar** y aborta. Justo lo contrario de lo que se buscaba.
- **Solución:** quitar `AppMutex` (y el `CreateMutexW` de `__main__.py`) y dejar que
  `CloseApplications=yes` + `CloseApplicationsFilter=Expoal.exe` cierren la app vía Windows
  Restart Manager, que SÍ funciona en silencioso. Verificado: `Installation process succeeded`,
  versión actualizada y app reabierta sola.
- **Gotcha del test:** no probar el instalador con `Start-Process -Wait`; como el setup relanza
  la app al terminar, `-Wait` se queda colgado esperando a que esa app se cierre.

## 2026-07-21 — "This video is not available" NO era yt-dlp viejo

- **Síntoma:** `youtu.be/NS8DsXzU2Xg` fallaba con "This video is not available" y la sospecha
  era que el yt-dlp instalado (2026.07.04) se había quedado viejo.
- **Diagnóstico:** con el yt-dlp MÁS NUEVO de PyPI (2026.7.4, el mismo) el vídeo seguía fallando
  y un vídeo de control (Big Buck Bunny) funcionaba. Conclusión: el vídeo está borrado, privado
  o bloqueado por región; no es bug de Expoal ni cuestión de versión.
- **Receta para la próxima vez:** probar el MISMO enlace con yt-dlp a pelo y un vídeo de control
  en la misma sesión. Si ambos fallan → motor viejo; si solo falla uno → es ese vídeo.
- **De regalo:** de esta investigación salió el motor actualizable (`engine.py`, v1.9.0), porque
  el caso "yt-dlp viejo rompe la app instalada" es real aunque esta vez no fuera eso.

## 2026-07-06 — Alinear el tagline del logo con "Expoal"

- **Problema:** "DEL LINK A TU DISCO" se veía descentrado respecto a "Expoal".
- **Causa raíz:** "Expoal" tiene descendente (la 'p'); con `align-items: center` el tagline se
  centra respecto a la line-box completa (que incluye el hueco del descendente), quedando por
  debajo del centro óptico de las mayúsculas.
- **Solución:** `line-height: 1` en h1 y tagline + `position: relative; top: -2px` en el tagline
  (valor elegido con `scripts/tune_header.py`, que compara offsets con una línea guía). OJO: el
  `.exe`/instalador empaquetan el CSS, así que un cambio de estilo obliga a recompilar y resubir
  los assets del release, no solo a pushear.
