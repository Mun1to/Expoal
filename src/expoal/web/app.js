"use strict";

const $ = (sel) => document.querySelector(sel);

/* ============================================================================
   IDIOMA (es / en)
   El español vive en el HTML y su traducción viaja al lado, en data-en (o
   data-en-placeholder / data-en-title / data-en-aria para los atributos): así
   texto y traducción se editan juntos y no hay forma de que se desincronicen.
   Los textos que escribe este archivo van en DICT. El idioma inicial lo fija
   el <script> del <head> antes de pintar, para que no se vea cambiar.
   ============================================================================ */
const I18N = (function () {
  const DICT = {
    es: {
      analyze: "Analizar", analyzing: "Analizando...",
      video: "Vídeo", best: "Máxima disponible", nochange: "sin cambios",
      neterror: "Error de red",
      nosubs: "Este vídeo no tiene subtítulos disponibles",
      cropbad: "El recorte deja el vídeo sin imagen",
      auto: (name) => `${name} (automático)`,
      videosize: (w, h) => `(vídeo de ${w}x${h} px)`,
      oftotal: (t) => `de ${t}`,
      cropresult: (from, to) => `${from} queda en ${to}`,
      needsffmpeg: "Requiere FFmpeg",
      download: "Descargar",
      updating: "Descargando la actualización... Expoal se reiniciará solo.",
      installing: "Instalando... la aplicación se cerrará en un momento.",
      enginedl: "Actualizando el motor...",
      enginedone: "Motor actualizado. Cierra y abre Expoal para estrenarlo.",
      cancel: "Cancelar descarga",
      openfolder: "Abrir la carpeta del archivo",
      filegone: "El archivo ya no está ahí",
      cookiesnone: "Sin cookies",
      cookiespick: "¿De dónde saco las cookies?",
      cookiesask: "Este vídeo pide iniciar sesión",
      cookiesactive: (b) => `Usando las cookies de ${b}`,
      argssaved: "Guardado, se aplicará a las próximas descargas",
      argscleared: "Sin opciones extra",
      playlist: "Lista de reproducción",
      plvideos: (n) => `${n} vídeo${n === 1 ? "" : "s"}`,
      plmore: (n) => `más de ${n} vídeos`,
      plselected: (n) => `${n} elegido${n === 1 ? "" : "s"}`,
      pladd: (n) => n ? `Añadir ${n} a la cola` : "Elige al menos un vídeo",
      cookiesfail: "No se han podido leer las cookies de ese navegador",
      cookiesfailhelp: "Ciérralo del todo y vuelve a probar. Si es Chrome o Edge en Windows, prueba con Firefox o exporta las cookies a un archivo: las versiones nuevas cifran las cookies de forma que Expoal no puede leerlas.",
      cookiesfileopt: "Archivo cookies.txt...",
      cookiesfileactive: "Usando un archivo de cookies",
      cookiesfilebad: "Ese archivo de cookies no existe",
      edges: "bordes", noaudio: "sin audio",
      pause: "Pausar la descarga", resume: "Reanudar la descarga",
      retry: "Reintentar", paused: "Pausada",
      logempty: "Todavía no hay nada. Analiza o descarga algo y aquí verás, paso a paso, lo que hace el motor.",
      loglost: "... (líneas antiguas descartadas)",
      copied: "Copiado", copyfail: "No se ha podido copiar",
      multiempty: "No hay ningún enlace en ese texto",
      multititle: "Enlaces pegados",
      multiready: (n, dup, bad) => {
        const parts = [`${n} enlace${n === 1 ? "" : "s"}`];
        if (dup) parts.push(`${dup} repetido${dup === 1 ? "" : "s"} quitado${dup === 1 ? "" : "s"}`);
        if (bad) parts.push(`${bad} línea${bad === 1 ? "" : "s"} sin enlace`);
        return parts.join(" · ");
      },
      needsaria2c: "Necesita aria2c instalado en el equipo",
      status: {
        en_cola: "En cola", descargando: "Descargando...", procesando: "Procesando...",
        editando: "Editando...", completado: "Completado", error: "Error",
        cancelado: "Cancelada",
      },
      badges: { audio: "MP3", text: "TEXTO" },
      mins: (m, s) => `${m}:${s} min`,
      hours: (h, m) => `${h}h ${m}m`,
    },
    en: {
      analyze: "Analyze", analyzing: "Analyzing...",
      video: "Video", best: "Best available", nochange: "no changes",
      neterror: "Network error",
      nosubs: "This video has no subtitles available",
      cropbad: "The crop leaves the video with no image",
      auto: (name) => `${name} (automatic)`,
      videosize: (w, h) => `(video, ${w}x${h} px)`,
      oftotal: (t) => `of ${t}`,
      cropresult: (from, to) => `${from} becomes ${to}`,
      needsffmpeg: "Requires FFmpeg",
      download: "Download",
      updating: "Downloading the update... Expoal will restart by itself.",
      installing: "Installing... the app will close in a moment.",
      enginedl: "Updating the engine...",
      enginedone: "Engine updated. Close and reopen Expoal to use it.",
      cancel: "Cancel download",
      openfolder: "Open the file's folder",
      filegone: "The file is not there anymore",
      cookiesnone: "No cookies",
      cookiespick: "Where should the cookies come from?",
      cookiesask: "This video asks you to sign in",
      cookiesactive: (b) => `Using cookies from ${b}`,
      argssaved: "Saved, it will apply to your next downloads",
      argscleared: "No extra options",
      playlist: "Playlist",
      plvideos: (n) => `${n} video${n === 1 ? "" : "s"}`,
      plmore: (n) => `more than ${n} videos`,
      plselected: (n) => `${n} selected`,
      pladd: (n) => n ? `Add ${n} to queue` : "Pick at least one video",
      cookiesfail: "Could not read the cookies from that browser",
      cookiesfailhelp: "Close it completely and try again. If it is Chrome or Edge on Windows, try Firefox instead or export your cookies to a file: recent versions encrypt cookies in a way Expoal cannot read.",
      cookiesfileopt: "cookies.txt file...",
      cookiesfileactive: "Using a cookies file",
      cookiesfilebad: "That cookies file does not exist",
      edges: "edges", noaudio: "no audio",
      pause: "Pause the download", resume: "Resume the download",
      retry: "Try again", paused: "Paused",
      logempty: "Nothing yet. Analyze or download something and you will see, step by step, what the engine does.",
      loglost: "... (older lines dropped)",
      copied: "Copied", copyfail: "Could not copy",
      multiempty: "There is no link in that text",
      multititle: "Pasted links",
      multiready: (n, dup, bad) => {
        const parts = [`${n} link${n === 1 ? "" : "s"}`];
        if (dup) parts.push(`${dup} duplicate${dup === 1 ? "" : "s"} removed`);
        if (bad) parts.push(`${bad} line${bad === 1 ? "" : "s"} with no link`);
        return parts.join(" · ");
      },
      needsaria2c: "Needs aria2c installed on this computer",
      status: {
        en_cola: "Queued", descargando: "Downloading...", procesando: "Processing...",
        editando: "Editing...", completado: "Done", error: "Error",
        cancelado: "Cancelled",
      },
      badges: { audio: "MP3", text: "TEXT" },
      mins: (m, s) => `${m}:${s} min`,
      hours: (h, m) => `${h}h ${m}m`,
    },
  };

  let lang = document.documentElement.lang === "en" ? "en" : "es";
  const listeners = [];

  function apply() {
    document.documentElement.lang = lang;
    for (const el of document.querySelectorAll("[data-en]")) {
      if (el.dataset.esText === undefined) el.dataset.esText = el.innerHTML.trim();
      // innerHTML seguro: la cadena está escrita en index.html (lleva <code>),
      // nunca procede de un vídeo ni de ninguna entrada externa.
      el.innerHTML = lang === "en" ? el.dataset.en : el.dataset.esText;
    }
    for (const el of document.querySelectorAll("[data-en-placeholder]")) {
      if (el.dataset.esPlaceholder === undefined) el.dataset.esPlaceholder = el.placeholder;
      el.placeholder = lang === "en" ? el.dataset.enPlaceholder : el.dataset.esPlaceholder;
    }
    for (const el of document.querySelectorAll("[data-en-title]")) {
      if (el.dataset.esTitle === undefined) el.dataset.esTitle = el.title;
      el.title = lang === "en" ? el.dataset.enTitle : el.dataset.esTitle;
      el.setAttribute("aria-label", el.title);
    }
    for (const el of document.querySelectorAll("[data-en-aria]")) {
      const es = el.dataset.esAria !== undefined
        ? el.dataset.esAria
        : (el.dataset.esAria = el.getAttribute("aria-label"));
      el.setAttribute("aria-label", lang === "en" ? el.dataset.enAria : es);
    }
    // El botón anuncia el idioma al que llevas, no el que ya tienes
    const btn = $("#lang");
    if (btn) {
      btn.textContent = lang === "es" ? "English" : "Español";
      btn.title = lang === "es" ? "Switch to English" : "Cambiar a español";
      btn.setAttribute("aria-label", btn.title);
    }
    for (const fn of listeners) fn(lang);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const btn = $("#lang");
    if (btn) {
      btn.addEventListener("click", () => {
        lang = lang === "es" ? "en" : "es";
        try { localStorage.setItem("expoal-lang", lang); } catch (e) { /* modo privado */ }
        apply();
      });
    }
    apply();
  });

  return {
    t: (k) => DICT[lang][k],
    lang: () => lang,
    onChange: (fn) => listeners.push(fn),
  };
})();

const state = {
  info: null,
  mode: "video",
  plMode: "video",   // modo de la playlist (solo vídeo o audio)
  subFormat: "txt",
  ffmpeg: false,
  // Edición del vídeo: recorte de duración (segundos), bordes (píxeles) y silenciado.
  edit: { start: 0, end: 0, duration: 0 },
  // Cookies del navegador: lista disponible, el elegido, y si hay un fallo que
  // resolver ("login" = el vídeo pide sesión, "fail" = no se pudieron leer).
  browsers: [],
  cookiesBrowser: "",
  cookiesFile: "",
  cookiesProblem: "",
  // null = decide la app (se abre si hay fallo o si ya hay cookies puestas);
  // true/false = el usuario lo abrió o lo cerró a mano, y entonces manda él.
  cookiesOpen: null,
  // La fila del archivo se queda abierta aunque todavía no haya ruta guardada:
  // si no, cancelar el explorador la cerraba y no había dónde escribirla.
  cookiesFileRow: false,
  // Trabajos fallidos que ya levantaron el aviso. Sin esto, la cola lo volvía a
  // levantar en cada refresco (cada 1,5 s) y el bloque era imposible de cerrar.
  cookiesSeen: [],
  // Opciones avanzadas de yt-dlp, tal cual las escribió el usuario.
  extraArgs: "",
  // Casillas de lo común (SponsorBlock, incrustar carátula...) y qué necesita
  // cada una para poder ofrecerse (FFmpeg, o el aria2c del sistema).
  toggles: {},
  togglesNeedFfmpeg: [],
  togglesNeedAria2c: [],
  aria2c: false,
  // Panel de terminal: si está abierto, por qué línea va y cuántas pinta.
  log: { open: false, cursor: 0, count: 0 },
  // Último recuento de la lista de enlaces pegados, para poder retraducirlo.
  multi: null,
  // Lo último que se pintó de la cola y del historial, para no reconstruirlos
  // cuando el servidor devuelve exactamente lo mismo (ver refresh).
  painted: { jobs: "", history: "" },
};

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = I18N.t("neterror");
    let extra = null;
    try {
      const data = await res.json();
      if (data && data.detail) {
        // El detalle puede venir como texto o, cuando el fallo tiene arreglo
        // (falta de sesión), como objeto con banderas para la interfaz.
        if (typeof data.detail === "object") {
          extra = data.detail;
          detail = String(data.detail.message || detail);
        } else {
          detail = String(data.detail);
        }
      }
    } catch (_) { /* respuesta sin JSON */ }
    const err = new Error(detail);
    if (extra) Object.assign(err, extra);
    throw err;
  }
  return res.json();
}

function post(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function showError(el, message) {
  el.textContent = message;
  el.classList.remove("hidden");
}

function hideError(el) {
  el.classList.add("hidden");
}

function formatDuration(seconds) {
  if (!seconds) return "";
  const s = Math.round(seconds);
  const m = Math.floor(s / 60);
  if (m >= 60) return I18N.t("hours")(Math.floor(m / 60), m % 60);
  return I18N.t("mins")(m, String(s % 60).padStart(2, "0"));
}

// --- Edición: tiempos ---

function parseTime(text) {
  // Acepta "90", "1:30" y "1:02:03". Devuelve segundos o null si no es válido.
  const parts = String(text).trim().split(":").map((p) => p.trim());
  if (parts.some((p) => p === "" || isNaN(Number(p)))) return null;
  return parts.reduce((total, p) => total * 60 + Number(p), 0);
}

function formatTime(seconds) {
  const s = Math.max(0, Math.round(seconds));
  const m = Math.floor(s / 60);
  const rest = String(s % 60).padStart(2, "0");
  if (m >= 60) return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}:${rest}`;
  return `${m}:${rest}`;
}

// --- Análisis del enlace ---

/* ============================================================================
   COOKIES DEL NAVEGADOR
   Muchos vídeos no fallan porque la app esté rota, sino porque la plataforma
   pide sesión iniciada (privados, con edad, de miembros, anti-bot). yt-dlp sabe
   leer las cookies del navegador que ya tienes abierto.
   El bloque NO se enseña de entrada: la mayoría de enlaces no lo necesitan y
   llenaría de preguntas la pantalla más simple de la app. Aparece cuando el
   fallo lo pide, y se queda en tono bajo mientras haya un navegador elegido.
   ============================================================================ */
function renderCookies() {
  const row = $("#cookies-row");
  const select = $("#cookies-select");
  const chosen = state.cookiesBrowser || "";
  const file = state.cookiesFile || "";
  // El desplegable solo se reconstruye cuando cambia lo que lleva dentro: la
  // lista de navegadores o el idioma ("Sin cookies" se traduce). Repoblarlo en
  // cada repintado lo cerraba de golpe si el usuario lo tenía desplegado.
  const sig = `${I18N.lang()}|${state.browsers.join(",")}`;
  if (select.dataset.sig !== sig) {
    select.dataset.sig = sig;
    select.innerHTML = "";
    const none = document.createElement("option");
    none.value = "";
    none.textContent = I18N.t("cookiesnone");
    select.appendChild(none);
    for (const b of state.browsers) {
      const opt = document.createElement("option");
      opt.value = b;
      // Los nombres de navegador son marcas: se muestran con mayúscula inicial.
      opt.textContent = b.charAt(0).toUpperCase() + b.slice(1);
      select.appendChild(opt);
    }
    // El archivo es la última opción de la misma lista, no otro sitio: para el
    // usuario es "de dónde saco las cookies", y el navegador o un archivo son
    // dos respuestas a esa única pregunta.
    const fileOpt = document.createElement("option");
    fileOpt.value = "file";
    fileOpt.textContent = I18N.t("cookiesfileopt");
    select.appendChild(fileOpt);
  }

  // La fila del archivo sigue abierta mientras esa sea la opción elegida,
  // aunque todavía no haya ruta: es donde se escribe a mano.
  const fileRow = state.cookiesFileRow || Boolean(file);
  // Si el usuario está encima del desplegable o del campo, no se le toca lo que
  // tiene delante: repintar es cosa de la app, elegir es cosa suya.
  if (document.activeElement !== select) select.value = fileRow ? "file" : chosen;
  $("#cookies-file-row").classList.toggle("hidden", !fileRow);
  if (document.activeElement !== $("#cookies-file-input")) $("#cookies-file-input").value = file;

  const title = $("#cookies-title");
  const help = $("#cookies-help");
  if (state.cookiesProblem === "fail") {
    title.textContent = I18N.t("cookiesfail");
    help.textContent = I18N.t("cookiesfailhelp");
  } else if (state.cookiesProblem === "login") {
    title.textContent = I18N.t("cookiesask");
    help.textContent = help.dataset.base || "";
  } else if (file) {
    title.textContent = I18N.t("cookiesfileactive");
    help.textContent = help.dataset.base || "";
  } else if (chosen) {
    title.textContent = I18N.t("cookiesactive")(
      chosen.charAt(0).toUpperCase() + chosen.slice(1)
    );
    help.textContent = help.dataset.base || "";
  } else {
    // Abierto a mano y sin nada elegido todavía: preguntar, en vez de decir
    // "Usando las cookies de " con el hueco vacío al final.
    title.textContent = I18N.t("cookiespick");
    help.textContent = help.dataset.base || "";
  }

  // Con problema, el bloque llama la atención y ofrece reintentar. Sin él, solo
  // recuerda en bajo que las cookies están puestas.
  const problem = Boolean(state.cookiesProblem);
  row.classList.toggle("quiet", !problem);
  $("#cookies-retry").classList.toggle("hidden", !problem);
  // La app PROPONE abrirlo (hay un fallo que resolver, o cookies ya puestas),
  // pero si el usuario lo abrió o lo cerró a mano gana su decisión: antes, con
  // un navegador elegido o un fallo en pantalla, no había forma de salir de ahí.
  const auto = problem || Boolean(chosen) || Boolean(file);
  const open = state.cookiesOpen === null ? auto : state.cookiesOpen;
  row.classList.toggle("hidden", !open);
  // El enlace y el bloque son la misma cosa en dos estados: nunca los dos.
  const toggle = $("#cookies-toggle");
  toggle.classList.toggle("hidden", open);
  // Cerrado y con cookies puestas, el enlace lo recuerda: si volviera a su
  // pregunta se perdería la única señal de que están activas.
  if (!open && (chosen || file)) {
    toggle.textContent = file
      ? I18N.t("cookiesfileactive")
      : I18N.t("cookiesactive")(chosen.charAt(0).toUpperCase() + chosen.slice(1));
  } else if (toggle.dataset.base) {
    toggle.textContent = toggle.dataset.base;
  }
}

/* Abrir y cerrar el bloque a mano. Un fallo nuevo vuelve a poner la decisión en
   manos de la app (`null`), para que el aviso salga aunque se cerrara antes. */
function openCookies(open) {
  state.cookiesOpen = open;
  renderCookies();
  if (open) $("#cookies-select").focus();
  else $("#cookies-toggle").focus();
}

function renderToggles() {
  for (const input of document.querySelectorAll("[data-toggle]")) {
    const name = input.dataset.toggle;
    input.checked = Boolean(state.toggles[name]);
    // Recortar patrocinios o incrustar cosas reescribe el archivo, y eso lo
    // hace FFmpeg; aria2c es un programa aparte que Expoal no instala. Sin lo
    // que hace falta, la casilla se apaga y dice por qué, en vez de dejar que
    // el usuario la marque y la descarga falle luego.
    let missing = "";
    if (state.togglesNeedFfmpeg.includes(name) && !state.ffmpeg) missing = I18N.t("needsffmpeg");
    else if (state.togglesNeedAria2c.includes(name) && !state.aria2c) missing = I18N.t("needsaria2c");
    input.disabled = Boolean(missing);
    input.closest(".toggle").title = missing;
  }
}

async function setToggle(name, value) {
  try {
    await post("/api/settings/toggle", { name, value });
    state.toggles[name] = value;
  } catch (err) {
    showError($("#url-error"), err.message);
    renderToggles();   // devuelve la casilla a su estado real
  }
}

async function saveExtraArgs() {
  const input = $("#args-input");
  const status = $("#args-status");
  const btn = $("#args-save");
  btn.disabled = true;
  try {
    const res = await post("/api/settings/args", { args: input.value });
    state.extraArgs = res.extra_args;
    status.className = "args-status ok";
    status.textContent = res.extra_args ? I18N.t("argssaved") : I18N.t("argscleared");
  } catch (err) {
    // El mensaje viene del propio yt-dlp ("no such option: --foo"), que es
    // exactamente lo que necesita quien escribe flags a mano.
    status.className = "args-status err";
    status.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

async function setCookiesBrowser(name) {
  const res = await post("/api/settings/cookies", { browser: name });
  state.cookiesBrowser = res.cookies_browser;
  state.cookiesFile = res.cookies_file || "";
  // Elegir un navegador (o "Sin cookies") es responder a la misma pregunta: la
  // fila del archivo sobra y se recoge.
  state.cookiesFileRow = false;
  // Elegir navegador es el intento de arreglo: se limpia el problema para que
  // el bloque no siga en rojo antes de saber si ha funcionado.
  state.cookiesProblem = "";
  renderCookies();
}

async function setCookiesFile(path) {
  const res = await post("/api/settings/cookies-file", { path });
  state.cookiesFile = res.cookies_file || "";
  state.cookiesBrowser = res.cookies_browser || "";
  state.cookiesFileRow = Boolean(state.cookiesFile);
  state.cookiesProblem = "";
  renderCookies();
}

/* Elegir "Archivo cookies.txt..." abre el explorador. Si el diálogo nativo no
   está disponible (o el usuario lo cancela) se deja igualmente la fila abierta
   con el campo de texto, para poder pegar la ruta a mano. */
async function chooseCookiesFile() {
  // Por estado, no tocando el DOM a mano: si no, el siguiente repintado cerraba
  // la fila y el usuario perdía el sitio donde estaba escribiendo la ruta.
  state.cookiesFileRow = true;
  renderCookies();
  let picked = null;
  try {
    const res = await api("/api/pick-file", { method: "POST" });
    picked = res.path;
  } catch (_) { /* sin diálogo: queda el campo de texto */ }
  if (picked) {
    try {
      await setCookiesFile(picked);
    } catch (err) {
      showError($("#url-error"), err.message);
    }
  } else {
    $("#cookies-file-input").focus();
  }
}

async function analyze(event) {
  if (event) event.preventDefault();
  const btn = $("#analyze-btn");
  const errorEl = $("#url-error");
  hideError(errorEl);
  btn.disabled = true;
  btn.textContent = I18N.t("analyzing");
  try {
    state.info = await post("/api/info", { url: $("#url-input").value });
    state.cookiesProblem = "";
    // Un enlace puede ser un vídeo o una lista entera: cada uno tiene su vista.
    if (state.info.type === "playlist") {
      $("#preview").classList.add("hidden");
      renderPlaylist();
    } else {
      $("#playlist").classList.add("hidden");
      renderPreview();
    }
  } catch (err) {
    $("#preview").classList.add("hidden");
    $("#playlist").classList.add("hidden");
    // Si el fallo tiene arreglo, se ofrece ahí mismo en vez de dejar al
    // usuario con un mensaje que no sabe cómo resolver.
    if (err.cookie_error) state.cookiesProblem = "fail";
    else if (err.needs_cookies) state.cookiesProblem = "login";
    // Un fallo nuevo devuelve la decisión a la app, para que el aviso salga
    // aunque el usuario hubiera cerrado el bloque en el intento anterior.
    if (state.cookiesProblem) state.cookiesOpen = null;
    // Cuando falla la lectura de cookies, el mensaje de yt-dlp es un volcado de
    // rutas del sistema: no aporta nada sobre lo que ya dice el bloque de abajo
    // en cristiano, y encima enseña la carpeta del usuario. Se calla.
    if (state.cookiesProblem === "fail") hideError(errorEl);
    else showError(errorEl, err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = I18N.t("analyze");
    renderCookies();
  }
}

function renderPreview() {
  const info = state.info;
  // Sin miniatura se esconde la imagen entera. Un src vacío no deja el hueco en
  // blanco: el navegador lo resuelve como la propia página, se la pide como si
  // fuera una imagen y acaba pintando el icono de imagen rota.
  const thumb = $("#preview-thumb");
  thumb.classList.toggle("hidden", !info.thumbnail);
  if (info.thumbnail) thumb.src = info.thumbnail;
  else thumb.removeAttribute("src");
  $("#preview-platform").textContent = info.platform || I18N.t("video");
  $("#preview-title").textContent = info.title || info.url;
  const parts = [];
  if (info.uploader) parts.push(info.uploader);
  if (info.duration) parts.push(formatDuration(info.duration));
  $("#preview-sub").textContent = parts.join(" · ");
  renderQualityOptions();
  renderOutFormats();
  renderSubtitleOptions();
  resetEdit();
  $("#preview").classList.remove("hidden");
}

function renderQualityOptions() {
  const select = $("#quality-select");
  select.innerHTML = "";
  select.disabled = state.mode !== "video";
  const best = document.createElement("option");
  best.value = "best";
  best.textContent = I18N.t("best");
  select.appendChild(best);
  if (state.mode === "video" && state.info) {
    for (const height of state.info.heights) {
      const opt = document.createElement("option");
      opt.value = String(height);
      opt.textContent = `${height}p`;
      select.appendChild(opt);
    }
  }
}

// --- Subtítulos / texto del vídeo ---

function renderOutFormats() {
  // El contenedor de vídeo o el códec de audio en que se guarda el archivo.
  const isText = state.mode === "text";
  $("#out-format-option").classList.toggle("hidden", isText || !state.ffmpeg);
  if (isText) return;
  const list = state.mode === "video"
    ? (state.info?.video_formats || ["mp4", "mkv", "mov", "webm"])
    : (state.info?.audio_formats || ["mp3", "m4a", "wav", "flac", "opus"]);
  const select = $("#out-format-select");
  const previous = select.value;
  select.innerHTML = "";
  for (const f of list) {
    const opt = document.createElement("option");
    opt.value = f;
    opt.textContent = f.toUpperCase();
    select.appendChild(opt);
  }
  // Por defecto, el de siempre: MP4 para vídeo y MP3 para audio.
  select.value = list.includes(previous) ? previous
    : (state.mode === "video" ? "mp4" : "mp3");
}

function renderSubtitleOptions() {
  const tracks = state.info?.subtitles || [];
  const select = $("#sub-lang-select");
  if (select.options.length !== tracks.length || select.dataset.url !== state.info?.url) {
    select.innerHTML = "";
    for (const t of tracks) {
      const opt = document.createElement("option");
      opt.value = t.code;
      opt.textContent = t.automatic ? I18N.t("auto")(t.name) : t.name;
      select.appendChild(opt);
    }
    select.dataset.url = state.info?.url || "";
    // Preseleccionamos español si existe; si no, el primero (propios van antes).
    const es = tracks.find((t) => t.code === "es" || t.code.startsWith("es-"));
    if (es) select.value = es.code;
  }

  const isText = state.mode === "text";
  const hasSubs = tracks.length > 0;
  // En modo texto el idioma y el formato mandan; la calidad no pinta nada.
  $("#quality-option").classList.toggle("hidden", isText);
  $("#sub-lang-option").classList.toggle("hidden", !isText || !hasSubs);
  $("#sub-format-option").classList.toggle("hidden", !isText || !hasSubs);
  // La casilla de "guardar también el texto" solo aplica al vídeo.
  $("#subs-check-row").classList.toggle("hidden", state.mode !== "video" || !hasSubs);
  if (state.mode !== "video") $("#subs-check").checked = false;

  const noSubs = isText && !hasSubs;
  $("#download-btn").disabled = noSubs;
  if (noSubs) {
    showError($("#download-error"), I18N.t("nosubs"));
  } else {
    hideError($("#download-error"));
  }
}

// --- Edición del vídeo ---

function cropValues() {
  return {
    top: Math.max(0, Number($("#crop-top").value) || 0),
    bottom: Math.max(0, Number($("#crop-bottom").value) || 0),
    left: Math.max(0, Number($("#crop-left").value) || 0),
    right: Math.max(0, Number($("#crop-right").value) || 0),
  };
}

function collectEdits() {
  const { start, end, duration } = state.edit;
  const crop = cropValues();
  const mute = $("#mute-check").checked;
  const trimmed = duration > 0 && (start > 0 || end < duration);
  const cropped = crop.top || crop.bottom || crop.left || crop.right;
  if (!trimmed && !cropped && !mute) return null;
  return {
    trim_start: trimmed && start > 0 ? start : null,
    trim_end: trimmed && end < duration ? end : null,
    crop_top: crop.top,
    crop_bottom: crop.bottom,
    crop_left: crop.left,
    crop_right: crop.right,
    mute,
  };
}

function renderCropPreview(crop, info, bad) {
  // Las franjas se colocan en porcentaje del vídeo, así la vista previa refleja
  // el recorte real sea cual sea el tamaño de la miniatura.
  const pct = (px, total) => `${Math.min(100, Math.max(0, (px / total) * 100))}%`;
  const top = pct(crop.top, info.height);
  const bottom = pct(crop.bottom, info.height);
  const left = pct(crop.left, info.width);
  const right = pct(crop.right, info.width);

  const shade = (side) => document.querySelector(`.crop-shade[data-side="${side}"]`);
  shade("top").style.height = top;
  shade("bottom").style.height = bottom;
  const sideLeft = shade("left");
  const sideRight = shade("right");
  sideLeft.style.width = left;
  sideRight.style.width = right;
  // Las franjas laterales solo cubren la parte que queda entre las horizontales.
  for (const el of [sideLeft, sideRight]) {
    el.style.top = top;
    el.style.bottom = bottom;
  }

  const frame = $("#crop-frame");
  frame.style.top = top;
  frame.style.bottom = bottom;
  frame.style.left = left;
  frame.style.right = right;
  frame.style.display = bad ? "none" : "block";
}

function renderEdit() {
  const { start, end, duration } = state.edit;

  // Barra y tiradores
  if (duration > 0) {
    const a = (start / duration) * 100;
    const b = (end / duration) * 100;
    $("#trim-sel").style.left = `${a}%`;
    $("#trim-sel").style.width = `${Math.max(0, b - a)}%`;
    $("#trim-h-start").style.left = `${a}%`;
    $("#trim-h-end").style.left = `${b}%`;
  }
  if (document.activeElement !== $("#trim-start")) $("#trim-start").value = formatTime(start);
  if (document.activeElement !== $("#trim-end")) $("#trim-end").value = formatTime(end);
  $("#trim-hint").textContent = duration ? I18N.t("oftotal")(formatTime(duration)) : "";

  // Recorte de bordes: tamaño resultante, aviso si es imposible y vista previa
  const crop = cropValues();
  const info = state.info || {};
  const result = $("#crop-result");
  if (info.width && info.height) {
    let w = info.width - crop.left - crop.right;
    let h = info.height - crop.top - crop.bottom;
    w -= w % 2;
    h -= h % 2;
    const bad = w <= 0 || h <= 0;
    result.classList.toggle("err", bad);
    result.textContent = bad
      ? I18N.t("cropbad")
      : I18N.t("cropresult")(`${info.width}x${info.height}`, `${w}x${h}`);
    renderCropPreview(crop, info, bad);
  } else {
    result.textContent = "";
  }

  // Resumen en la cabecera plegable
  const parts = [];
  if (duration > 0 && (start > 0 || end < duration)) {
    parts.push(`${formatTime(start)}-${formatTime(end)}`);
  }
  if (crop.top || crop.bottom || crop.left || crop.right) parts.push(I18N.t("edges"));
  if ($("#mute-check").checked) parts.push(I18N.t("noaudio"));
  const summary = $("#edit-summary");
  summary.textContent = parts.length ? parts.join(" · ") : I18N.t("nochange");
  $("#edit-toggle").classList.toggle("dirty", parts.length > 0);
}

function setupEdit() {
  $("#edit-toggle").addEventListener("click", () => {
    const body = $("#edit-body");
    const open = body.classList.toggle("hidden");
    $("#edit-toggle").setAttribute("aria-expanded", String(!open));
  });

  // Arrastre de los tiradores sobre la barra
  const bar = $("#trim-bar");
  const posToTime = (clientX) => {
    const r = bar.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (clientX - r.left) / r.width));
    return ratio * state.edit.duration;
  };
  const drag = (which) => (ev) => {
    if (!state.edit.duration) return;
    ev.preventDefault();
    const move = (e) => {
      const t = posToTime(e.clientX);
      if (which === "start") state.edit.start = Math.min(t, state.edit.end - 0.5);
      else state.edit.end = Math.max(t, state.edit.start + 0.5);
      state.edit.start = Math.max(0, state.edit.start);
      state.edit.end = Math.min(state.edit.duration, state.edit.end);
      renderEdit();
    };
    const up = () => {
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", up);
    };
    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", up);
  };
  $("#trim-h-start").addEventListener("pointerdown", drag("start"));
  $("#trim-h-end").addEventListener("pointerdown", drag("end"));

  // Flechas del teclado para ajuste fino (accesibilidad)
  const nudge = (which) => (ev) => {
    const step = ev.shiftKey ? 5 : 1;
    if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
    ev.preventDefault();
    const delta = ev.key === "ArrowLeft" ? -step : step;
    if (which === "start") {
      state.edit.start = Math.max(0, Math.min(state.edit.start + delta, state.edit.end - 0.5));
    } else {
      state.edit.end = Math.min(state.edit.duration, Math.max(state.edit.end + delta, state.edit.start + 0.5));
    }
    renderEdit();
  };
  $("#trim-h-start").addEventListener("keydown", nudge("start"));
  $("#trim-h-end").addEventListener("keydown", nudge("end"));

  // Campos de texto: escribir el tiempo mueve los tiradores
  const applyField = (which) => () => {
    const el = which === "start" ? $("#trim-start") : $("#trim-end");
    const t = parseTime(el.value);
    if (t === null || !state.edit.duration) return renderEdit();
    if (which === "start") {
      state.edit.start = Math.max(0, Math.min(t, state.edit.end - 0.5));
    } else {
      state.edit.end = Math.min(state.edit.duration, Math.max(t, state.edit.start + 0.5));
    }
    renderEdit();
  };
  $("#trim-start").addEventListener("change", applyField("start"));
  $("#trim-end").addEventListener("change", applyField("end"));
  $("#trim-start").addEventListener("blur", applyField("start"));
  $("#trim-end").addEventListener("blur", applyField("end"));

  $("#trim-reset").addEventListener("click", () => {
    state.edit.start = 0;
    state.edit.end = state.edit.duration;
    renderEdit();
  });

  for (const id of ["#crop-top", "#crop-bottom", "#crop-left", "#crop-right"]) {
    $(id).addEventListener("input", renderEdit);
  }
  $("#mute-check").addEventListener("change", renderEdit);
}

function resetEdit() {
  const duration = Number(state.info?.duration) || 0;
  state.edit = { start: 0, end: duration, duration };
  for (const id of ["#crop-top", "#crop-bottom", "#crop-left", "#crop-right"]) $(id).value = 0;
  $("#mute-check").checked = false;
  const info = state.info || {};
  $("#crop-hint").textContent = info.width
    ? I18N.t("videosize")(info.width, info.height)
    : "";
  // La vista previa toma la proporción real del vídeo (no la de la miniatura, que
  // en YouTube siempre viene en 16:9 aunque el vídeo sea vertical).
  const preview = $("#crop-preview");
  if (info.width && info.height) {
    preview.style.aspectRatio = `${info.width} / ${info.height}`;
    // Fijamos solo el lado largo y dejamos que el otro lo calcule el aspecto: así
    // un vídeo vertical (Twitter, Shorts) no se estira ni desborda el panel.
    const vertical = info.height > info.width;
    preview.style.height = vertical ? "184px" : "auto";
    preview.style.width = vertical ? "auto" : "150px";
    $("#crop-preview-img").src = info.thumbnail || "";
    preview.classList.remove("hidden");
  } else {
    preview.classList.add("hidden");
  }
  // La edición solo aplica a vídeo, y necesita FFmpeg.
  const usable = state.mode === "video" && duration > 0 && state.ffmpeg;
  $("#edit-section").classList.toggle("hidden", !usable);
  $("#edit-body").classList.add("hidden");
  $("#edit-toggle").setAttribute("aria-expanded", "false");
  renderEdit();
}

/* ============================================================================
   PLAYLIST
   Cuando el enlace es una lista o un canal, en vez del preview de un vídeo se
   muestra la lista de vídeos con casillas. Comparten formato, calidad y carpeta;
   cada vídeo elegido se encola como un trabajo normal. Sin edición por vídeo (el
   mismo recorte en 30 vídeos no tiene sentido) ni modo texto.
   Las opciones globales (SponsorBlock, cookies, incrustar...) se aplican igual,
   porque viven en los ajustes y se leen al descargar, sea un vídeo o una lista.
   ============================================================================ */
const QUALITY_LADDER = ["2160", "1440", "1080", "720", "480", "360"];

/* Varios enlaces pegados a la vez. Se limpian en el servidor (misma limpieza
   para todos, y con tests) y se muestran en la MISMA vista de la playlist: la
   tarea es idéntica —elegir de una lista y encolar con opciones comunes—, así
   que reutilizarla es una pantalla menos que mantener y una menos que aprender.
   No se pide el título de cada vídeo: serían N peticiones de red antes de
   empezar, y el título real aparece solo en la cola en cuanto arranca. */
async function prepareMulti() {
  const btn = $("#multi-prepare");
  const status = $("#multi-status");
  btn.disabled = true;
  try {
    const res = await post("/api/urls/clean", { text: $("#multi-input").value });
    if (!res.urls.length) {
      status.className = "args-status err";
      status.textContent = I18N.t("multiempty");
      $("#playlist").classList.add("hidden");
      return;
    }
    status.className = "args-status ok";
    // Se guarda el recuento, no solo el texto: al cambiar de idioma hay que
    // poder volver a escribirlo (lo escribe este archivo, no lleva data-en).
    state.multi = res;
    status.textContent = I18N.t("multiready")(res.urls.length, res.duplicates, res.invalid);
    state.info = {
      type: "playlist",
      pasted: true,        // el título lo ponemos nosotros: hay que retraducirlo
      title: I18N.t("multititle"),
      uploader: "",
      count: res.urls.length,
      truncated: res.truncated,
      entries: res.urls.map((url) => ({ url, title: url, duration: null })),
    };
    $("#preview").classList.add("hidden");
    renderPlaylist();
    $("#playlist").scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (err) {
    status.className = "args-status err";
    status.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
}

function fmtDur(seconds) {
  const s = Number(seconds) || 0;
  if (!s) return "";
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  const two = (n) => String(n).padStart(2, "0");
  return h ? `${h}:${two(m)}:${two(sec)}` : `${m}:${two(sec)}`;
}

function renderPlaylist() {
  const info = state.info;
  $("#pl-title").textContent = info.title || I18N.t("playlist");
  const parts = [];
  if (info.uploader) parts.push(info.uploader);
  // Si la lista se cortó en el tope, se dice claramente: "más de N".
  parts.push(info.truncated ? I18N.t("plmore")(info.count) : I18N.t("plvideos")(info.count));
  $("#pl-sub").textContent = parts.join(" · ");

  // Calidad: escalera fija (las entradas ligeras no traen formatos por vídeo).
  const q = $("#pl-quality-select");
  q.innerHTML = "";
  const best = document.createElement("option");
  best.value = "best";
  best.textContent = I18N.t("best");
  q.appendChild(best);
  for (const h of QUALITY_LADDER) {
    const opt = document.createElement("option");
    opt.value = h;
    opt.textContent = `${h}p`;
    q.appendChild(opt);
  }
  renderPlModeUI();

  if (!$("#pl-folder-input").value) $("#pl-folder-input").value = $("#folder-input").value;

  // La lista de vídeos, todos marcados de entrada.
  const ul = $("#pl-list");
  ul.innerHTML = "";
  info.entries.forEach((e, i) => {
    const li = document.createElement("li");
    li.className = "pl-item";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = true;
    cb.dataset.idx = String(i);
    cb.addEventListener("change", updatePlCount);
    const num = document.createElement("span");
    num.className = "pl-num";
    num.textContent = String(i + 1);
    const name = document.createElement("span");
    name.className = "pl-name";
    name.textContent = e.title;          // textContent: el título es entrada externa
    name.title = e.title;
    const dur = document.createElement("span");
    dur.className = "pl-dur";
    dur.textContent = fmtDur(e.duration);
    li.append(cb, num, name, dur);
    // Clic en toda la fila alterna la casilla, salvo si se pulsa la casilla misma.
    li.addEventListener("click", (ev) => {
      if (ev.target !== cb) { cb.checked = !cb.checked; updatePlCount(); }
    });
    ul.appendChild(li);
  });

  updatePlCount();
  $("#playlist").classList.remove("hidden");
}

function renderPlModeUI() {
  const isAudio = state.plMode === "audio";
  const list = isAudio
    ? (state.info?.audio_formats || ["mp3", "m4a", "wav", "flac", "opus"])
    : (state.info?.video_formats || ["mp4", "mkv", "mov", "webm"]);
  $("#pl-quality-select").disabled = isAudio;   // el audio no tiene resolución
  $("#pl-format-option").classList.toggle("hidden", !state.ffmpeg);
  const sel = $("#pl-format-select");
  const previous = sel.value;
  sel.innerHTML = "";
  for (const f of list) {
    const opt = document.createElement("option");
    opt.value = f;
    opt.textContent = f.toUpperCase();
    sel.appendChild(opt);
  }
  sel.value = list.includes(previous) ? previous : (isAudio ? "mp3" : "mp4");
}

function plChecks() {
  return [...document.querySelectorAll("#pl-list input[type=checkbox]")];
}

function updatePlCount() {
  const n = plChecks().filter((c) => c.checked).length;
  $("#pl-selected").textContent = I18N.t("plselected")(n);
  const btn = $("#pl-add");
  btn.textContent = I18N.t("pladd")(n);
  btn.disabled = n === 0;
}

async function addPlaylist() {
  const btn = $("#pl-add");
  const errorEl = $("#pl-error");
  hideError(errorEl);
  const chosen = plChecks().filter((c) => c.checked).map((c) => state.info.entries[Number(c.dataset.idx)]);
  if (!chosen.length) return;
  btn.disabled = true;
  try {
    // El formato solo se manda si se pudo elegir (sin FFmpeg no hay selector).
    const hasFormat = !$("#pl-format-option").classList.contains("hidden");
    await post("/api/download-batch", {
      items: chosen.map((e) => ({ url: e.url, title: e.title })),
      mode: state.plMode,
      quality: $("#pl-quality-select").value,
      folder: $("#pl-folder-input").value,
      out_format: hasFormat ? $("#pl-format-select").value : "",
    });
    $("#playlist").classList.add("hidden");
    $("#url-input").value = "";
    state.info = null;
    await refresh();
  } catch (err) {
    showError(errorEl, err.message);
    updatePlCount();   // devuelve el botón a su estado
  }
}

// --- Descarga ---

async function download() {
  const btn = $("#download-btn");
  const errorEl = $("#download-error");
  hideError(errorEl);
  btn.disabled = true;
  try {
    await post("/api/download", {
      url: state.info.url,
      mode: state.mode,
      quality: $("#quality-select").value,
      folder: $("#folder-input").value,
      title: state.info.title,
      edits: state.mode === "video" ? collectEdits() : null,
      subs: state.mode === "video" && $("#subs-check").checked,
      sub_lang: $("#sub-lang-select").value || "",
      sub_format: state.subFormat,
      out_format: state.mode === "text" ? "" : $("#out-format-select").value,
    });
    $("#preview").classList.add("hidden");
    $("#url-input").value = "";
    state.info = null;
    await refresh();
  } catch (err) {
    showError(errorEl, err.message);
  } finally {
    btn.disabled = false;
  }
}

/* ============================================================================
   TERMINAL — lo que hace el motor por detrás
   Cuando algo falla o tarda, "Error" no dice nada. Este panel enseña la salida
   real de yt-dlp: qué extractor entró, qué formato eligió, si está fusionando.
   No se enseña de entrada (la app tiene que seguir siendo simple); se enciende
   con el botón de la cabecera y se queda encendido hasta que se apague.
   El sondeo lleva un cursor: solo se pide lo nuevo desde la última línea vista.
   ============================================================================ */
const LOG_MAX_NODES = 600;   // por encima de esto se recortan las más viejas

function logNotice(text) {
  const view = $("#log-view");
  const row = document.createElement("div");
  row.className = "log-empty";
  row.textContent = text;
  view.appendChild(row);
}

function appendLogLines(lines) {
  const view = $("#log-view");
  if (state.log.count === 0) view.textContent = "";   // fuera el aviso de vacío
  const frag = document.createDocumentFragment();
  for (const ln of lines) {
    const row = document.createElement("div");
    row.className = `l-${ln.level}`;
    const time = document.createElement("span");
    time.className = "t";
    // El espacio va en el texto, no solo en el CSS: al copiar el panel, la
    // hora y el mensaje tienen que salir separados.
    time.textContent = `${ln.at} `;
    // textContent, nunca innerHTML: esto viene de yt-dlp y lleva dentro
    // títulos de vídeo, que son entrada externa.
    row.append(time, document.createTextNode(ln.text));
    frag.appendChild(row);
  }
  view.appendChild(frag);
  state.log.count += lines.length;
  while (state.log.count > LOG_MAX_NODES && view.firstChild) {
    view.removeChild(view.firstChild);
    state.log.count -= 1;
  }
  if ($("#log-follow").checked) view.scrollTop = view.scrollHeight;
}

async function pollLog() {
  if (!state.log.open) return;
  try {
    const res = await api(`/api/log?after=${state.log.cursor}`);
    if (res.lost) logNotice(I18N.t("loglost"));
    if (res.lines && res.lines.length) appendLogLines(res.lines);
    state.log.cursor = res.cursor;
    if (state.log.count === 0) {
      $("#log-view").textContent = "";
      logNotice(I18N.t("logempty"));
    }
  } catch (_) {
    // El servidor puede estar arrancando; se reintenta en el siguiente ciclo.
  }
}

function setLogOpen(open) {
  state.log.open = open;
  $("#log-section").classList.toggle("hidden", !open);
  $("#log-toggle").classList.toggle("active", open);
  try { localStorage.setItem("expoal-log", open ? "1" : "0"); } catch (e) { /* modo privado */ }
  if (open) {
    // Al abrir se pide todo el buffer: interesa lo que ya pasó, no solo lo que
    // venga a partir de ahora.
    state.log.cursor = 0;
    state.log.count = 0;
    $("#log-view").textContent = "";
    pollLog();
  }
}

// --- Cola e historial ---

// Iconos de los botones de fila. innerHTML seguro: cadenas constantes de este
// archivo, jamás construidas con datos del vídeo.
const ICON_X =
  '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';
const ICON_FOLDER =
  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/></svg>';
const ICON_PAUSE =
  '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
  '<rect x="6" y="5" width="4" height="14" rx="1"/><rect x="14" y="5" width="4" height="14" rx="1"/></svg>';
const ICON_PLAY =
  '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
  '<path d="M8 5.5v13l11-6.5z"/></svg>';
const ICON_RETRY =
  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
  '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/></svg>';

function iconButton(icon, title) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "icon-btn row-btn";
  btn.innerHTML = icon;
  btn.title = title;
  btn.setAttribute("aria-label", title);
  return btn;
}

function folderButton(path) {
  const btn = iconButton(ICON_FOLDER, I18N.t("openfolder"));
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    try {
      await post("/api/open-folder", { path });
    } catch (_) {
      // Da igual si fue 403 o 404: para quien mira, el archivo no aparece.
      btn.classList.add("err");
      btn.title = I18N.t("filegone");
      btn.setAttribute("aria-label", btn.title);
    } finally {
      btn.disabled = false;
    }
  });
  return btn;
}

function renderJob(job) {
  const item = document.createElement("div");
  item.className = "job";

  const head = document.createElement("div");
  head.className = "job-head";
  const title = document.createElement("span");
  title.className = "job-title";
  title.textContent = job.title || job.url;
  const status = document.createElement("span");
  status.className = "job-status";
  if (job.status === "completado") status.classList.add("ok");
  if (job.status === "error") status.classList.add("err");
  let statusText = I18N.t("status")[job.status] || job.status;
  if (job.status === "descargando") {
    statusText = job.paused ? `${I18N.t("paused")} · ${job.progress}%` : `${job.progress}%`;
    // Pausado no se enseñan velocidad ni tiempo restante: son la última medida
    // de antes de parar, y anunciar "3 MB/s" de algo que no se mueve es mentira.
    if (!job.paused) {
      if (job.speed) statusText += ` · ${job.speed}`;
      if (job.eta) statusText += ` · ${job.eta}`;
    }
  }
  status.textContent = statusText;
  head.append(title, status);

  // Botón de acción que llama al endpoint y refresca; el patrón se repite en
  // pausar, reanudar y reintentar, así que va una vez.
  const actionButton = (icon, label, path, extraClass) => {
    const btn = iconButton(icon, label);
    if (extraClass) btn.classList.add(extraClass);
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try {
        await api(path, { method: "POST" });
        refresh();
      } catch (_) {
        btn.disabled = false;
      }
    });
    return btn;
  };

  // Pausar solo mientras descarga: en cola no ha empezado, y con FFmpeg
  // trabajando no hay nada que pausar.
  if (job.status === "descargando") {
    head.appendChild(job.paused
      ? actionButton(ICON_PLAY, I18N.t("resume"), `/api/jobs/${job.id}/resume`)
      : actionButton(ICON_PAUSE, I18N.t("pause"), `/api/jobs/${job.id}/pause`));
  }
  if (job.status === "error" || job.status === "cancelado") {
    head.appendChild(actionButton(ICON_RETRY, I18N.t("retry"), `/api/jobs/${job.id}/retry`));
  }
  if (job.status === "en_cola" || job.status === "descargando") {
    head.appendChild(
      actionButton(ICON_X, I18N.t("cancel"), `/api/jobs/${job.id}/cancel`, "job-cancel")
    );
  }
  if (job.status === "completado" && job.file_path) {
    head.appendChild(folderButton(job.file_path));
  }
  item.appendChild(head);

  if (job.status === "descargando" || job.status === "procesando" || job.status === "en_cola") {
    const bar = document.createElement("div");
    bar.className = "progress";
    const fill = document.createElement("div");
    fill.style.width = `${job.status === "procesando" ? 100 : job.progress}%`;
    bar.appendChild(fill);
    item.appendChild(bar);
  }

  if (job.status === "error" && job.error) {
    const err = document.createElement("p");
    err.className = "job-error";
    err.textContent = job.error;
    item.appendChild(err);
    // Si la descarga murió por falta de sesión, se levanta el bloque de cookies
    // arriba: el arreglo está ahí y si no, el usuario se queda sin salida.
    // Una vez por trabajo, NO "mientras no haya problema": el trabajo fallido
    // sigue en la cola, así que la segunda condición lo levantaba otra vez en
    // cada refresco y el bloque revivía en cuanto lo cerrabas o elegías algo.
    if (job.needs_cookies && !state.cookiesSeen.includes(job.id)) {
      state.cookiesSeen.push(job.id);
      state.cookiesProblem = "login";
      state.cookiesOpen = null;   // un fallo nuevo vuelve a proponer abrirlo
      renderCookies();
    }
  }

  if (job.status === "completado" && job.file_path) {
    const path = document.createElement("p");
    path.className = "job-path";
    path.textContent = job.file_path;
    item.appendChild(path);
  }

  return item;
}

/* Reintentar una descarga del historial: se vuelve a encolar con las mismas
   opciones que tenía (modo, calidad, carpeta y formato se guardan justo para
   esto). Sirve tanto para repetir una que salió bien como para recuperar una
   que falló hace días, que es el caso que de verdad importa. */
function historyRetryButton(entry) {
  const btn = iconButton(ICON_RETRY, I18N.t("retry"));
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    try {
      await post("/api/download", {
        url: entry.url,
        mode: entry.mode || "video",
        quality: entry.quality || "best",
        folder: entry.folder || "",
        title: entry.title || "",
        sub_lang: entry.sub_lang || "",
        sub_format: entry.sub_format || "txt",
        out_format: entry.out_format || "",
      });
      await refresh();
    } catch (err) {
      btn.classList.add("err");
      btn.title = err.message;
      btn.setAttribute("aria-label", err.message);
      btn.disabled = false;
    }
  });
  return btn;
}

function renderHistoryItem(entry) {
  const item = document.createElement("div");
  item.className = "history-item";
  const failed = entry.status === "error";
  if (failed) item.classList.add("err");

  const head = document.createElement("div");
  head.className = "history-head";
  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = failed
    ? I18N.t("status").error
    : (I18N.t("badges")[entry.mode] || entry.platform || I18N.t("video"));
  const title = document.createElement("span");
  title.className = "history-title";
  title.textContent = entry.title || entry.url;
  const date = document.createElement("span");
  date.className = "history-date";
  date.textContent = (entry.downloaded_at || "").replace("T", " ");
  head.append(badge, title, date);
  head.appendChild(historyRetryButton(entry));
  if (entry.file_path) head.appendChild(folderButton(entry.file_path));
  item.appendChild(head);

  if (failed && entry.error) {
    const err = document.createElement("p");
    err.className = "history-error";
    err.textContent = entry.error;
    item.appendChild(err);
  }

  if (entry.file_path) {
    const path = document.createElement("p");
    path.className = "history-path";
    path.textContent = entry.file_path;
    item.appendChild(path);
  }

  return item;
}

async function refresh() {
  try {
    const [jobs, historyEntries] = await Promise.all([
      api("/api/jobs"),
      api("/api/history"),
    ]);

    // Reconstruir las listas solo cuando de verdad cambian. Hacerlo en cada
    // ciclo (40 veces por minuto) borraba el aviso en rojo de "el archivo ya no
    // está" antes de que diera tiempo a leerlo, y tiraba el foco del teclado de
    // los botones de fila. Al cambiar de idioma se invalidan estas firmas a
    // mano, porque los textos de estado los escribe este archivo.
    const queueList = $("#queue-list");
    const jobsSig = JSON.stringify(jobs);
    if (jobsSig !== state.painted.jobs) {
      state.painted.jobs = jobsSig;
      queueList.replaceChildren(...jobs.map(renderJob));
    }
    $("#queue-section").classList.toggle("hidden", jobs.length === 0);
    // "Limpiar terminadas" solo cuando hay algo que limpiar, y "reintentar
    // fallidas" solo cuando hay fallos: en una lista de cuarenta vídeos es la
    // diferencia entre recuperarlos de un clic o buscarlos uno a uno.
    const doneStates = ["completado", "error", "cancelado"];
    const hasDone = jobs.some((j) => doneStates.includes(j.status));
    $("#clear-queue").classList.toggle("hidden", !hasDone);
    const hasFailed = jobs.some((j) => j.status === "error" || j.status === "cancelado");
    $("#retry-failed").classList.toggle("hidden", !hasFailed);

    const historyList = $("#history-list");
    const historySig = JSON.stringify(historyEntries);
    if (historySig !== state.painted.history) {
      state.painted.history = historySig;
      historyList.replaceChildren(...historyEntries.map(renderHistoryItem));
    }
    $("#history-section").classList.toggle("hidden", historyEntries.length === 0);
  } catch (_) {
    // El servidor puede estar arrancando; se reintenta en el siguiente ciclo.
  }
  // El panel de terminal se refresca en el mismo ciclo que la cola: es la misma
  // cadencia y así no hay un segundo temporizador dando vueltas.
  pollLog();
}

// --- Arranque ---

async function init() {
  $("#url-form").addEventListener("submit", analyze);
  $("#download-btn").addEventListener("click", download);
  $("#clear-history").addEventListener("click", async () => {
    await api("/api/history", { method: "DELETE" });
    refresh();
  });
  $("#clear-queue").addEventListener("click", async () => {
    await api("/api/jobs", { method: "DELETE" });
    refresh();
  });
  $("#retry-failed").addEventListener("click", async () => {
    await api("/api/jobs/retry-failed", { method: "POST" });
    refresh();
  });

  // Terminal: se abre con el botón de la cabecera y recuerda si quedó abierta.
  $("#log-toggle").addEventListener("click", () => setLogOpen(!state.log.open));
  $("#log-clear").addEventListener("click", async () => {
    try { await api("/api/log", { method: "DELETE" }); } catch (_) { /* da igual */ }
    state.log.cursor = 0;
    state.log.count = 0;
    $("#log-view").textContent = "";
    logNotice(I18N.t("logempty"));
  });
  $("#log-copy").addEventListener("click", async () => {
    const btn = $("#log-copy");
    const before = btn.textContent;
    try {
      await navigator.clipboard.writeText($("#log-view").innerText);
      btn.textContent = I18N.t("copied");
    } catch (_) {
      btn.textContent = I18N.t("copyfail");
    }
    setTimeout(() => { btn.textContent = before; }, 1600);
  });

  for (const btn of document.querySelectorAll("#mode-group button")) {
    btn.addEventListener("click", () => {
      state.mode = btn.dataset.mode;
      for (const b of document.querySelectorAll("#mode-group button")) {
        b.classList.toggle("active", b === btn);
      }
      renderQualityOptions();
      renderOutFormats();
      // La sección de edición y los subtítulos dependen del modo elegido.
      if (state.info) {
        renderSubtitleOptions();
        resetEdit();
      }
    });
  }

  // El explorador nativo lo abre el servidor (corre en el mismo PC), así que
  // funciona igual en el navegador y en la ventana de escritorio.
  const pickInto = async (btn, input) => {
    btn.disabled = true;
    try {
      const res = await api("/api/pick-folder", { method: "POST" });
      if (res.folder) input.value = res.folder;
    } catch (_) {
      // Si el diálogo no está disponible, queda el cuadro de texto.
    } finally {
      btn.disabled = false;
    }
  };
  $("#folder-btn").addEventListener("click", () => pickInto($("#folder-btn"), $("#folder-input")));

  // Playlist: modo (vídeo/audio), elegir/quitar todos, carpeta y añadir.
  for (const btn of document.querySelectorAll("#pl-mode-group button")) {
    btn.addEventListener("click", () => {
      state.plMode = btn.dataset.plmode;
      for (const b of document.querySelectorAll("#pl-mode-group button")) {
        b.classList.toggle("active", b === btn);
      }
      renderPlModeUI();
    });
  }
  const setAllPl = (checked) => { plChecks().forEach((c) => { c.checked = checked; }); updatePlCount(); };
  $("#pl-all").addEventListener("click", () => setAllPl(true));
  $("#pl-none").addEventListener("click", () => setAllPl(false));
  $("#pl-folder-btn").addEventListener("click", () => pickInto($("#pl-folder-btn"), $("#pl-folder-input")));
  $("#pl-add").addEventListener("click", addPlaylist);

  $("#theme-toggle").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("expoal-theme", next);
    // Reflow síncrono: algunos motores no re-resuelven los var() de los
    // descendientes al cambiar el atributo; esto fuerza el recálculo sin parpadeo.
    document.body.style.display = "none";
    void document.body.offsetHeight;
    document.body.style.display = "";
  });

  // Dos textos de las cookies viven en el HTML (con su data-en) y este archivo
  // los pisa a ratos: la ayuda larga, para enseñar un fallo, y el enlace, para
  // recordar qué cookies hay puestas. Hay que guardar el original para poder
  // devolverlos. Se registra ANTES del primer await de init(): así el pintado
  // inicial de I18N ya llama aquí y la base queda en el idioma que toca (init
  // sigue corriendo después de ese pintado, y guardarla a mano antes dejaría la
  // versión en español metida en la app en inglés).
  const cookiesHelp = $("#cookies-help");
  const cookiesToggle = $("#cookies-toggle");
  const saveCookieBases = () => {
    cookiesHelp.dataset.base = cookiesHelp.textContent;
    cookiesToggle.dataset.base = cookiesToggle.textContent;
  };
  saveCookieBases();
  I18N.onChange(saveCookieBases);

  try {
    const cfg = await api("/api/config");
    $("#version").textContent = `v${cfg.version}`;
    $("#folder-input").value = cfg.default_folder;
    state.ffmpeg = cfg.ffmpeg;
    state.aria2c = Boolean(cfg.aria2c);
    state.browsers = cfg.browsers || [];
    state.cookiesBrowser = cfg.cookies_browser || "";
    state.cookiesFile = cfg.cookies_file || "";
    state.extraArgs = cfg.extra_args || "";
    state.toggles = cfg.toggles || {};
    state.togglesNeedFfmpeg = cfg.toggles_need_ffmpeg || [];
    state.togglesNeedAria2c = cfg.toggles_need_aria2c || [];
    $("#args-input").value = state.extraArgs;
    renderToggles();
    // Si ya hay algo puesto, el panel se abre solo: son ajustes invisibles que
    // afectan a todas las descargas, así que esconderlos confundiría.
    if (state.extraArgs || Object.values(state.toggles).some(Boolean)) {
      $("#args-row").classList.remove("hidden");
    }
    renderCookies();
    if (!cfg.ffmpeg) {
      $("#ffmpeg-banner").classList.remove("hidden");
      const audioBtn = $("#audio-btn");
      audioBtn.disabled = true;
      audioBtn.title = I18N.t("needsffmpeg");
    }
  } catch (_) { /* se reintenta al refrescar */ }

  $("#cookies-select").addEventListener("change", (e) => {
    // "file" no es un navegador: abre el explorador para elegir el cookies.txt.
    if (e.target.value === "file") {
      chooseCookiesFile();
      return;
    }
    setCookiesBrowser(e.target.value).catch((err) => {
      showError($("#url-error"), err.message);
    });
  });
  $("#cookies-file-btn").addEventListener("click", chooseCookiesFile);
  // Escribir la ruta a mano también vale: en el .exe sin ventana no hay
  // diálogo nativo, y quedarse sin salida por eso sería absurdo.
  $("#cookies-file-input").addEventListener("change", async (e) => {
    try {
      await setCookiesFile(e.target.value.trim());
    } catch (err) {
      showError($("#url-error"), err.message);
      renderCookies();
    }
  });
  $("#cookies-retry").addEventListener("click", () => analyze());
  $("#cookies-toggle").addEventListener("click", () => openCookies(true));
  $("#cookies-close").addEventListener("click", () => openCookies(false));
  // Escape cierra el bloque desde cualquier campo suyo: es lo que hace todo el
  // mundo sin pensar cuando quiere salir de algo.
  $("#cookies-row").addEventListener("keydown", (e) => {
    if (e.key === "Escape") { e.preventDefault(); openCookies(false); }
  });
  $("#args-toggle").addEventListener("click", () => {
    $("#args-row").classList.toggle("hidden");
    if (!$("#args-row").classList.contains("hidden")) $("#args-input").focus();
  });
  $("#multi-toggle").addEventListener("click", () => {
    $("#multi-row").classList.toggle("hidden");
    if (!$("#multi-row").classList.contains("hidden")) $("#multi-input").focus();
  });
  $("#multi-prepare").addEventListener("click", prepareMulti);
  // Ctrl+Enter prepara la lista: mismo atajo que guardar las opciones, porque
  // los dos son campos de varias líneas donde Enter hace falta para escribir.
  $("#multi-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); prepareMulti(); }
  });
  $("#args-save").addEventListener("click", saveExtraArgs);
  for (const input of document.querySelectorAll("[data-toggle]")) {
    input.addEventListener("change", () => setToggle(input.dataset.toggle, input.checked));
  }
  // Ctrl+Enter guarda: es un campo de una línea larga, no un formulario, y
  // obligar a soltar el teclado para pulsar el botón molesta.
  $("#args-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); saveExtraArgs(); }
  });

  for (const btn of document.querySelectorAll("#sub-format-group button")) {
    btn.addEventListener("click", () => {
      state.subFormat = btn.dataset.subfmt;
      for (const b of document.querySelectorAll("#sub-format-group button")) {
        b.classList.toggle("active", b === btn);
      }
    });
  }

  setupEdit();

  // Los textos que escribe este archivo no llevan data-en, así que al cambiar
  // de idioma hay que repintar lo que ya esté en pantalla.
  I18N.onChange(() => {
    // La cola y el historial se repintan en el siguiente refresh(), pero solo
    // si su firma cambió, y el idioma no la cambia: hay que invalidarla aquí o
    // se quedarían en el idioma anterior hasta la siguiente descarga.
    state.painted.jobs = "";
    state.painted.history = "";
    // El bloque de cookies se repinta siempre (existe aunque no haya vídeo).
    // Las bases ya están guardadas en el idioma nuevo: saveCookieBases se
    // registró antes que este listener y los avisa I18N en orden.
    renderCookies();
    // Los avisos de las casillas ("Requiere FFmpeg", "Necesita aria2c") van en
    // el title, que lo escribe este archivo: sin repintar aquí se quedaban en
    // el idioma anterior (cazado con el barrido de traducciones).
    renderToggles();
    // El aviso de "aquí no hay nada todavía" es de este archivo: si el panel
    // está abierto y vacío, hay que volver a escribirlo en el idioma nuevo.
    if (state.log.open && state.log.count === 0) {
      $("#log-view").textContent = "";
      logNotice(I18N.t("logempty"));
    }
    if (state.multi) {
      const m = state.multi;
      $("#multi-status").textContent = I18N.t("multiready")(m.urls.length, m.duplicates, m.invalid);
    }
    if (!state.info) return;
    if (state.info.type === "playlist") {
      // Repintado ligero: NO reconstruir la lista o se perderían las casillas
      // que el usuario haya tocado. Solo se retraducen los textos.
      const info = state.info;
      const parts = [];
      if (info.uploader) parts.push(info.uploader);
      parts.push(info.truncated ? I18N.t("plmore")(info.count) : I18N.t("plvideos")(info.count));
      $("#pl-sub").textContent = parts.join(" · ");
      // El de una lista real es el título del sitio y no se toca; el de una
      // lista pegada a mano lo escribimos nosotros, así que se traduce.
      if (info.pasted) {
        info.title = I18N.t("multititle");
        $("#pl-title").textContent = info.title;
      }
      const best = $("#pl-quality-select").options[0];
      if (best) best.textContent = I18N.t("best");
      updatePlCount();
      return;
    }
    // renderSubtitleOptions solo repuebla el select si cambia el vídeo; al
    // cambiar de idioma el vídeo es el mismo, así que hay que invalidarlo a
    // mano o el "(automático)" se quedaría en el idioma anterior.
    $("#sub-lang-select").dataset.url = "";
    renderPreview();
    renderSubtitleOptions();
    renderEdit();
  });

  // El panel de terminal vuelve como se dejó: quien lo usa, lo usa siempre.
  try {
    if (localStorage.getItem("expoal-log") === "1") setLogOpen(true);
  } catch (e) { /* modo privado */ }

  checkForUpdate();
  refresh();
  setInterval(refresh, 1500);
}

async function checkForUpdate() {
  let info;
  try {
    info = await api("/api/update/check");
  } catch (_) {
    return; // sin conexión: no molestamos
  }
  if (!info) return;

  // Si hay app nueva se ofrece esa (trae el motor al día); si no, y el motor
  // (yt-dlp) se ha quedado viejo, se ofrece renovar solo el motor.
  if (!info.update_available) {
    if (info.engine && info.engine.update_available) showEngineBanner(info.engine);
    return;
  }

  const banner = $("#update-banner");
  $("#update-version").textContent = `v${info.latest}`;
  const notes = $("#update-notes");
  if (info.notes_url) notes.href = info.notes_url;
  else notes.classList.add("hidden");

  const btn = $("#update-btn");
  const status = $("#update-status");

  if (info.can_auto_install) {
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      status.classList.remove("hidden", "err");
      status.textContent = I18N.t("updating");
      try {
        await api("/api/update/apply", { method: "POST" });
        status.textContent = I18N.t("installing");
      } catch (err) {
        status.classList.add("err");
        status.textContent = err.message;
        btn.disabled = false;
      }
    });
  } else {
    // En modo web/navegador no hay instalador: el botón lleva a la descarga.
    btn.textContent = I18N.t("download");
    btn.addEventListener("click", () => {
      window.open(info.notes_url || "https://github.com/Mun1to/Expoal/releases/latest", "_blank");
    });
  }

  banner.classList.remove("hidden");
}

function showEngineBanner(engineInfo) {
  const banner = $("#engine-banner");
  $("#engine-version").textContent = `yt-dlp ${engineInfo.latest}`;
  const btn = $("#engine-btn");
  const status = $("#engine-status");
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    status.classList.remove("hidden", "err");
    status.textContent = I18N.t("enginedl");
    try {
      await api("/api/update/engine", { method: "POST" });
      status.textContent = I18N.t("enginedone");
      btn.classList.add("hidden");
    } catch (err) {
      status.classList.add("err");
      status.textContent = err.message;
      btn.disabled = false;
    }
  });
  banner.classList.remove("hidden");
}

init();
