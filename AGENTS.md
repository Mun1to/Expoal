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
- **UI bilingüe es/en** (app y landing, mismo patrón): el español vive en el HTML y su
  traducción al lado, en `data-en` (y `data-en-placeholder` / `data-en-title` / `data-en-aria`
  para atributos), así texto y traducción se editan juntos. Los textos que escribe el JS van en
  el diccionario `DICT` del módulo `I18N` (arriba de `app.js`). El idioma se fija en el `<script>`
  del `<head>` ANTES de pintar (localStorage > idioma del navegador) para que no se vea cambiar,
  y se recuerda en `expoal-lang`. GOTCHA: `renderSubtitleOptions()` solo repuebla el select si
  cambia el vídeo, así que al cambiar de idioma hay que invalidar `#sub-lang-select.dataset.url`
  a mano o el "(automático)" se queda en el idioma anterior. Al traducir algo nuevo que pinte el
  JS, acuérdate de repintarlo en el `I18N.onChange` de `init()`.
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
- **Marca**: ver [docs/MARCA.md](docs/MARCA.md). Logo de Munir (play azul dentro de flecha de
  descarga); azul de marca **#0069FF** sacado del propio logo. Los iconos NO se editan a mano: se
  generan con `scripts/make_brand.py` desde `assets/logo.png` (lienzo blanco redondeado, porque el
  logo es negro y se perdería sobre fondos oscuros). El `.foldericon.ico` de la carpeta es una copia
  de `assets/expoal.ico` (lo referencia `desktop.ini`).
- **Subtítulos / texto**: `subtitles.py`. `languages(info)` lista los idiomas (propios primero,
  automáticos después) desde `subtitles` + `automatic_captions`. `to_text()` limpia el SRT/VTT:
  quita tiempos, etiquetas y **las líneas repetidas** (los subtítulos automáticos repiten la frase
  anterior en cada cue). Tres modos en la UI: `video`, `audio` y `text`; en `text` se usa
  `skip_download=True` y el job devuelve el .txt/.srt como `file_path`. En modo vídeo, la casilla
  `subs` los guarda aparte. `writeautomaticsub=True` actúa de respaldo si no hay subtítulos propios.
- **Formatos de salida**: `VIDEO_FORMATS`/`AUDIO_FORMATS` en `downloader.py`. Vídeo por remux
  (`FFmpegVideoRemuxer`, casi instantáneo); audio por `FFmpegExtractAudio`. GOTCHA: el contenedor
  condiciona el CÓDEC, así que `_format_selector` recibe `out_format` y pide códecs compatibles:
  MOV exige `vcodec^=avc1` (YouTube sirve AV1 y el remux a MOV falla con "Conversion failed"),
  y WEBM prefiere `ext=webm` para no recodificar. MKV admite cualquier cosa.
- **Edición de vídeo**: `editor.py` post-procesa con FFmpeg lo ya descargado (`Edits`: trim_start/end,
  crop por lados, mute). Regla de coste: si NO hay recorte de bordes se copian los flujos (`-c copy`,
  instantáneo); con crop hay que recodificar (libx264 veryfast). El crop fuerza dimensiones pares
  (H.264 lo exige) y rechaza recortes que dejen el vídeo sin imagen. Se aplica solo en modo vídeo.
  La UI es una sección plegable con barra de dos tiradores + campos de tiempo sincronizados.
- **Auto-update**: `updater.py` consulta el último release del repo oficial (solo GitHub por HTTPS),
  compara semver, descarga el instalador, verifica `SHA256SUMS.txt` si existe y lo lanza en silent.
  Endpoints `/api/update/check` y `/api/update/apply`. La UI muestra un banner (aviso + 1 clic).
  Multiplataforma: en Windows baja el instalador `.exe` y lo lanza en silencioso; en Linux baja el
  `.AppImage` y **se reemplaza a sí mismo** (`running_appimage()` lee la variable `APPIMAGE`). En
  Linux sí se puede sobrescribir un ejecutable en uso: el proceso conserva el inodo viejo hasta
  salir. El archivo se descarga AL LADO del AppImage para que `os.replace` sea atómico (el rename
  solo lo es dentro del mismo sistema de archivos). `can_auto_install` es False fuera del empaquetado.
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
- **Landing (`site/index.html`, un solo archivo)**: el hero ocupa la pantalla entera
  (`.hero-wrap` con `position: sticky`) y **el resto de la página es una lámina** (`main.sheet`,
  fondo SÓLIDO y borde redondeado arriba) que **sube y lo tapa** al scrollear. Pedido así por
  Munir tres veces: si `.sheet` se vuelve transparente o el hero deja de ser sticky, el efecto
  desaparece. Al scrollear, cada `<section data-rise>` sube ENTERA como una tarjeta y sus hijos
  `[data-reveal]` solo se encienden en cascada de opacidad; el observer marca la sección y sus
  hijos de una vez para que no entren a destiempo. GOTCHA: `body` usa `overflow-x: clip` y no
  `hidden`, porque `hidden` convierte el body en contenedor de scroll y rompe el sticky.
  La **demo** arranca cerrada con un enlace de ejemplo `readonly` (no se edita a propósito): al
  pulsar Analizar se monta por pasos (`[data-step]`). **Idioma es/en**: el español está en el HTML
  y la traducción en `data-en` del mismo elemento; el `<script>` del `<head>` fija `html.lang`
  antes de pintar (`?lang=` > localStorage > idioma del navegador). Los textos que genera el JS
  van en el diccionario `DICT` de `I18N`.
- **Capturas/OG**: `scripts/capture_screenshots.py` (README/landing) y `scripts/make_og.py` (redes)
  con Playwright; requieren el server en :8710, y hay que arrancarlo DESPUÉS de subir la versión o
  la captura saldrá con la vieja (el número lo sirve el backend). Genera cuatro,
  `screenshot-{dark,light}-{es,en}.png`. Decisiones: el historial de ejemplo se inyecta
  interceptando `/api/history` con `page.route` (así el script no toca el historial real de nadie y
  sale igual en cualquier máquina), la carpeta de destino se reescribe a `C:\Users\You\...` porque
  las capturas se publican, y **no se usa `full_page`**: la página entera sale como una tira
  vertical que parece captura de web, mientras que al alto de la ventana se lee como app. Si tocas
  las capturas, cópialas también a `site/assets/` (la landing sirve desde ahí) y regenera la OG.
  `scripts/capture_header.py` es solo para revisar la alineación del logo (su salida
  `assets/header-check.png` no se versiona).
- **Prueba visible del producto**: la landing tiene, después de los puntos fuertes, una sección con
  la captura REAL enmarcada como ventana (`.shot`) que dice explícitamente que la demo de arriba es
  una recreación. Nació de feedback externo ("add pictures how the app actually looks"): antes solo
  se veía la demo simulada y la gente no sabía si la app existía. La imagen cambia con el idioma vía
  `data-en-src` (mismo patrón que `data-en`, resuelto en `apply()`). El README, por lo mismo,
  responde de frente a "is it just a yt-dlp wrapper?" en vez de dejar la pregunta en el aire.
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
