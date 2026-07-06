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
