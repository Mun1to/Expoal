# Expoal — Guía para agentes

Descargador de vídeos **100% local y open source**: pegas un link de YouTube/TikTok/Instagram
y el vídeo cae en tu disco. Sin webs de terceros, sin anuncios, sin subir nada a ningún sitio.

Proyecto independiente de Munir (repo público). Correlacionado con **Rolyal** (ambos comparten
el paso «link → vídeo descargado»), pero **sin core compartido por ahora**: si Rolyal lo
necesita más adelante, se extraerá lo común entonces.

## Reglas comunes multi-proyecto

Lee y aplica **[../Reglas_de_los_proyectos.md](../Reglas_de_los_proyectos.md)** (dictado por voz,
entender antes de arreglar, ciberseguridad, cerrar explicando, README/commits en inglés,
lluvia de ideas ante decisiones con entidad, pnpm en proyectos Node, guion normal en lo público,
trato «Munito»/«socio», nunca Co-Authored-By, preguntar antes de push, confirmar la intención
antes de ejecutar preguntando hasta estar seguro, simplicidad primero con cambios quirúrgicos
(código mínimo, tocar solo lo que la tarea pide y verificar contra el objetivo antes de dar por
hecho), arranque estructurado (investigar el stack y montar los cimientos AGENTS.md/README/docs/METAS.md
antes de programar: el plano antes que los ladrillos), y cerrar en una frase (lo hecho en una línea
arriba, los pasos siguientes debajo, el detalle largo solo si aporta)).

Antes de cualquier tarea, lee [FEEDBACK.md](FEEDBACK.md) para no repetir errores pasados.

## Stack y arquitectura

- **Python 3.10+** gestionado con **uv** (`uv sync`, `uv run expoal`).
- **FastAPI + uvicorn**: API local en `127.0.0.1` (nunca exponer a la red — decisión de seguridad).
- **yt-dlp** como librería (no como subproceso): extracción de info y descargas.
- **pywebview**: el modo escritorio (`--desktop`) abre la MISMA interfaz web en ventana nativa.
  Un solo código, dos modos. El selector nativo de carpetas solo existe en escritorio (js_api).
- **Frontend**: HTML/CSS/JS vanilla en `src/expoal/web/` (sin framework, estilo Moneorq).
- **FFmpeg**: opcional pero necesario para MP3 y para fusionar calidades máximas.
  `config.find_ffmpeg()` lo busca en PATH y en la carpeta de paquetes de winget.

## Estructura

```
src/expoal/
├─ __main__.py     # CLI: modo web (navegador) y modo --desktop (pywebview)
├─ server.py       # FastAPI: /api/info, /api/download, /api/jobs, /api/history, /api/config
├─ downloader.py   # DownloadManager: cola secuencial en un thread + progress hooks de yt-dlp
├─ history.py      # Historial JSON persistido en el dir de datos del usuario (platformdirs)
├─ config.py       # Rutas + detección de ffmpeg
└─ web/            # Interfaz (index.html, styles.css, app.js) — paleta Fundación Orquio
```

## Decisiones tomadas (no re-litigar sin motivo)

- **Servidor solo en 127.0.0.1**: es una app personal, no se expone a la LAN.
  Además hay un middleware `local_origin_guard` que bloquea POST con Origin externo
  (anti-CSRF contra el servidor local).
- **Cola secuencial** (un worker): suficiente para el MVP; concurrencia es meta futura.
- **UI en español** por ahora; i18n a inglés es meta futura (ver docs/METAS.md).
- **Tema claro/oscuro** vía `html[data-theme]` + variables CSS; el JS fuerza un reflow al
  cambiar (ver FEEDBACK.md). El tema inicial se fija en un `<script>` inline en el `<head>`
  para evitar el parpadeo (FOUC).
- **Explorador de carpetas** (`dialogs.pick_folder`): en escritorio usa el diálogo de pywebview;
  en web lanza un subproceso con tkinter (evita el problema de tkinter fuera del hilo principal);
  en el .exe congelado sin ventana devuelve None y la UI mantiene el cuadro de texto.
- **Empaquetado**: `launcher.py` es el entry point de PyInstaller (abre `--desktop` por defecto).
  Comando de build en el README. El icono se genera con `scripts/make_icon.ps1` (System.Drawing)
  y se empaqueta a .ico con `scripts/pack_ico.py`. `dist/`, `build/` y `*.spec` van en .gitignore.
- **Instalador**: `installer/expoal.iss` (Inno Setup 6, ISCC en `%LOCALAPPDATA%\Programs\Inno Setup 6`).
  Instala sin admin (PrivilegesRequired=lowest), crea accesos y desinstalador. `AppId` es un GUID
  fijo: NO cambiarlo entre versiones (identifica la app para updates/uninstall). Genera
  `dist/Expoal-<version>-setup.exe`. La versión se inyecta con `ISCC /DMyAppVersion=x.y.z`
  (el `#ifndef` deja un default). `CloseApplications=yes` + `AppMutex=ExpoalRunningMutex`
  (creado en `__main__`) permiten que el auto-update cierre y reabra la app.
- **Auto-update**: `updater.py` consulta el último release del repo oficial (solo GitHub por HTTPS),
  compara semver, descarga el instalador, verifica `SHA256SUMS.txt` si existe y lo lanza en silent.
  Endpoints `/api/update/check` y `/api/update/apply`. La UI muestra un banner (aviso + 1 clic);
  `can_auto_install` es True solo en el .exe empaquetado (en web el banner enlaza a la descarga).
- **Release automático**: `.github/workflows/release.yml` se dispara con un tag `v*`. Tiene 4 jobs:
  `version` (lee `__version__` y verifica que el tag coincide), `build-windows` (exe + instalador +
  zip), `build-linux` (AppImage) y `release` (junta artifacts, genera checksums y publica). La
  versión canónica es `__version__`. Para sacar versión: subir `__version__` + `pyproject`, commit,
  y `git push origin vX.Y.Z`.
- **Linux (AppImage)**: PyInstaller **no cross-compila**, por eso el build de Linux corre en
  `ubuntu-latest`. Gotchas: el separador de `--add-data` es `:` en Linux (`;` en Windows), no se usa
  `--windowed`, y `appimagetool` necesita `--appimage-extract-and-run` (el runner no tiene FUSE).
  En Linux la app abre en el **navegador** a propósito: pywebview depende de WebKitGTK del sistema y
  no empaqueta fiable entre distros (por eso `launcher.py` solo añade `--desktop` en win32).
  El auto-update solo aplica a Windows (`can_auto_install` exige `sys.platform == "win32"`), porque
  el asset es un instalador `.exe`; en Linux el banner enlaza a la descarga.
- **Capturas/OG**: `scripts/capture_screenshots.py` (README/landing) y `scripts/make_og.py` (redes)
  con Playwright; requieren server en :8710 e historial de ejemplo (Blender) escrito temporalmente
  en `%LOCALAPPDATA%\Expoal\history.json` y restaurado después. `scripts/capture_header.py` es
  solo para revisar la alineación del logo (su salida `assets/header-check.png` no se versiona).
- **Títulos de vídeo = entrada externa**: en el frontend SIEMPRE `textContent`, nunca
  `innerHTML` (XSS). En el backend, `windowsfilenames: True` sanea nombres de archivo.
- **Sin cookies/login**: contenido privado o con verificación de edad falla de forma
  esperada; soporte de `cookiesfrombrowser` es meta futura.
- **noplaylist: True**: solo vídeos sueltos en el MVP.

## Comandos

```bash
uv sync                    # instalar dependencias
uv run expoal --no-browser # servidor web en http://127.0.0.1:8710
uv run expoal --desktop    # ventana de escritorio
```

## froede (edición visual de webs)

Munir edita las webs de sus proyectos en localhost con **froede** (`C:\proyectos\froede`): extensión de navegador + companion local que escriben los cambios DIRECTAMENTE en los archivos fuente. Si aparecen diffs sin commit con `style={{ ... }}` inline nuevos, atributos `style="..."`/`href`/`alt`/`title` cambiados o textos editados, seguramente son ediciones intencionales de Munir hechas con froede: acéptalas y consérvalas, NO las reviertas ni las "normalices" (p. ej. moverlas a clases CSS) salvo que él lo pida. Notas: `data-froede-loc` solo existe en el DOM en dev (nunca llega a los archivos); `.froede-token` es un secreto local que debe estar en `.gitignore` y jamás commitearse. Regla completa: `C:\proyectos\Reglas_de_los_proyectos.md` (regla M).
