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
