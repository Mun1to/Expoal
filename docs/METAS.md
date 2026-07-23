# Metas de Expoal 🎮

Progreso por niveles, sin fechas. Cada meta desbloquea la siguiente.

## Nivel 1 — MVP jugable ✅

- [x] Pegar link → analizar → descargar a máxima calidad
- [x] Elegir formato (MP4 / MP3) y resolución
- [x] Carpeta de destino por descarga (con selector nativo en escritorio)
- [x] Cola con progreso en vivo (%, velocidad, ETA)
- [x] Historial persistente con botón de vaciado
- [x] Modo web y modo escritorio con un solo código
- [x] Detección de FFmpeg (PATH + winget) con aviso en la UI

## Nivel 2 — Pulido de producto ✅

- [x] Modo claro/oscuro con toggle persistente (recuerda elección, sigue al sistema por defecto)
- [x] Rediseño profesional: plano, glow sutil, tipografía y branding propios (icono + favicon)
- [x] Explorador de archivos nativo para elegir carpeta (funciona en web y en escritorio)
- [x] Empaquetado como Expoal.exe (PyInstaller) anclable a la barra de tareas
- [x] Edición al vuelo: recortar duración (barra visual + tiempos), recortar bordes por píxeles
      y quitar el audio del MP4 (`editor.py` con FFmpeg)
- [x] Elegir formato de salida: MP4/MKV/MOV/WEBM y MP3/M4A/WAV/FLAC/OPUS
- [x] Cancelar una descarga en curso (botón ✕, limpia los `.part`) y limpiar los trabajos
      terminados de la cola (v1.9.0)
- [x] i18n: interfaz en inglés además de español (v1.8.0, patrón `data-en` + `DICT`)
- [x] Abrir la carpeta del archivo descargado desde la UI (historial y cola, v1.9.0)

## Nivel 3 — Ecosistema

- [x] Instalador con Inno Setup (accesos directos automáticos, desinstalador) — `installer/expoal.iss`
- [x] Auto-actualización con un clic (banner en la app) + release automático con GitHub Actions
- [x] Build para **Linux** (AppImage, abre en el navegador) publicado junto al .exe de Windows
- [x] Auto-actualización también en Linux (el AppImage se reemplaza a sí mismo)
- [x] Extraer subtítulos: modo "Texto" (en vez del vídeo) y casilla para guardarlos junto al vídeo;
      salida en texto limpio o `.srt` con tiempos, eligiendo idioma
- [x] **Motor actualizable** (v1.9.0): yt-dlp se renueva desde la app sin reinstalarla
      (`engine.py`; el punto más frágil del producto, YouTube cambia cada pocas semanas)
- [x] **Cookies del navegador** (v2.1.0): desbloquea privados, con edad, de miembros y los
      anti-bot de YouTube. El backend distingue "falta sesión" de "no pude leer las cookies" y
      la interfaz ofrece el arreglo donde falla, en vez de soltar un error sin salida
- [x] **Opciones avanzadas de yt-dlp** (v2.1.0): campo libre con flags de la documentación
      oficial, validados al guardar. Cubre de golpe lo que la interfaz no expone, sin llenarla
      de casillas ni tener que implementar cada opción una a una
- [ ] Build para macOS (.dmg / .app) — requiere runner macOS
- [ ] Playlists y perfiles completos (hoy `noplaylist: True`; decisión de producto pendiente)
- [ ] Extraer `expoal-core` si Rolyal lo necesita en su servidor
- [ ] Descargar solo un fragmento SIN bajar el vídeo entero (hoy el recorte de duración
      descarga todo y corta después; esto sería ahorro de datos, no una función nueva)
