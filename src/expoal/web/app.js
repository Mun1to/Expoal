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
      cookiesask: "Este vídeo pide iniciar sesión",
      cookiesactive: (b) => `Usando las cookies de ${b}`,
      cookiesfail: "No se han podido leer las cookies de ese navegador",
      cookiesfailhelp: "Ciérralo del todo y vuelve a probar. Si es Chrome o Edge en Windows, prueba con Firefox: las versiones nuevas cifran las cookies de forma que Expoal no puede leerlas.",
      edges: "bordes", noaudio: "sin audio",
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
      cookiesask: "This video asks you to sign in",
      cookiesactive: (b) => `Using cookies from ${b}`,
      cookiesfail: "Could not read the cookies from that browser",
      cookiesfailhelp: "Close it completely and try again. If it is Chrome or Edge on Windows, try Firefox instead: recent versions encrypt cookies in a way Expoal cannot read.",
      edges: "edges", noaudio: "no audio",
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
  subFormat: "txt",
  ffmpeg: false,
  // Edición del vídeo: recorte de duración (segundos), bordes (píxeles) y silenciado.
  edit: { start: 0, end: 0, duration: 0 },
  // Cookies del navegador: lista disponible, el elegido, y si hay un fallo que
  // resolver ("login" = el vídeo pide sesión, "fail" = no se pudieron leer).
  browsers: [],
  cookiesBrowser: "",
  cookiesProblem: "",
  cookiesOpen: false,
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
  // El desplegable se repuebla al cambiar de idioma ("Sin cookies" se traduce).
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
  select.value = chosen;

  const title = $("#cookies-title");
  const help = $("#cookies-help");
  if (state.cookiesProblem === "fail") {
    title.textContent = I18N.t("cookiesfail");
    help.textContent = I18N.t("cookiesfailhelp");
  } else if (state.cookiesProblem === "login") {
    title.textContent = I18N.t("cookiesask");
    help.textContent = help.dataset.base || "";
  } else {
    title.textContent = I18N.t("cookiesactive")(
      chosen.charAt(0).toUpperCase() + chosen.slice(1)
    );
    help.textContent = help.dataset.base || "";
  }

  // Con problema, el bloque llama la atención y ofrece reintentar. Sin él, solo
  // recuerda en bajo que las cookies están puestas.
  const problem = Boolean(state.cookiesProblem);
  row.classList.toggle("quiet", !problem);
  $("#cookies-retry").classList.toggle("hidden", !problem);
  const open = problem || chosen || state.cookiesOpen;
  row.classList.toggle("hidden", !open);
  // El enlace y el bloque son la misma cosa en dos estados: nunca los dos.
  $("#cookies-toggle").classList.toggle("hidden", Boolean(open));
}

async function setCookiesBrowser(name) {
  const res = await post("/api/settings/cookies", { browser: name });
  state.cookiesBrowser = res.cookies_browser;
  // Elegir navegador es el intento de arreglo: se limpia el problema para que
  // el bloque no siga en rojo antes de saber si ha funcionado.
  state.cookiesProblem = "";
  renderCookies();
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
    renderPreview();
  } catch (err) {
    $("#preview").classList.add("hidden");
    // Si el fallo tiene arreglo, se ofrece ahí mismo en vez de dejar al
    // usuario con un mensaje que no sabe cómo resolver.
    if (err.cookie_error) state.cookiesProblem = "fail";
    else if (err.needs_cookies) state.cookiesProblem = "login";
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
  $("#preview-thumb").src = info.thumbnail || "";
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
    statusText = `${job.progress}%`;
    if (job.speed) statusText += ` · ${job.speed}`;
    if (job.eta) statusText += ` · ${job.eta}`;
  }
  status.textContent = statusText;
  head.append(title, status);
  if (job.status === "en_cola" || job.status === "descargando") {
    const cancel = iconButton(ICON_X, I18N.t("cancel"));
    cancel.classList.add("job-cancel");
    cancel.addEventListener("click", async () => {
      cancel.disabled = true;
      try {
        await api(`/api/jobs/${job.id}/cancel`, { method: "POST" });
        refresh();
      } catch (_) {
        cancel.disabled = false;
      }
    });
    head.appendChild(cancel);
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
    if (job.needs_cookies && !state.cookiesProblem) {
      state.cookiesProblem = "login";
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

function renderHistoryItem(entry) {
  const item = document.createElement("div");
  item.className = "history-item";

  const head = document.createElement("div");
  head.className = "history-head";
  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = I18N.t("badges")[entry.mode] || entry.platform || I18N.t("video");
  const title = document.createElement("span");
  title.className = "history-title";
  title.textContent = entry.title || entry.url;
  const date = document.createElement("span");
  date.className = "history-date";
  date.textContent = (entry.downloaded_at || "").replace("T", " ");
  head.append(badge, title, date);
  if (entry.file_path) head.appendChild(folderButton(entry.file_path));
  item.appendChild(head);

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

    const queueList = $("#queue-list");
    queueList.replaceChildren(...jobs.map(renderJob));
    $("#queue-section").classList.toggle("hidden", jobs.length === 0);
    // "Limpiar terminadas" solo cuando hay algo que limpiar.
    const doneStates = ["completado", "error", "cancelado"];
    const hasDone = jobs.some((j) => doneStates.includes(j.status));
    $("#clear-queue").classList.toggle("hidden", !hasDone);

    const historyList = $("#history-list");
    historyList.replaceChildren(...historyEntries.map(renderHistoryItem));
    $("#history-section").classList.toggle("hidden", historyEntries.length === 0);
  } catch (_) {
    // El servidor puede estar arrancando; se reintenta en el siguiente ciclo.
  }
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
  $("#folder-btn").addEventListener("click", async () => {
    const folderBtn = $("#folder-btn");
    folderBtn.disabled = true;
    try {
      const res = await api("/api/pick-folder", { method: "POST" });
      if (res.folder) $("#folder-input").value = res.folder;
    } catch (_) {
      // Si el diálogo no está disponible, queda el cuadro de texto.
    } finally {
      folderBtn.disabled = false;
    }
  });

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

  // El texto largo de ayuda de las cookies vive en el HTML (con su data-en);
  // se guarda antes de tocarlo para poder restaurarlo tras enseñar un fallo.
  const cookiesHelp = $("#cookies-help");
  cookiesHelp.dataset.base = cookiesHelp.textContent;

  try {
    const cfg = await api("/api/config");
    $("#version").textContent = `v${cfg.version}`;
    $("#folder-input").value = cfg.default_folder;
    state.ffmpeg = cfg.ffmpeg;
    state.browsers = cfg.browsers || [];
    state.cookiesBrowser = cfg.cookies_browser || "";
    renderCookies();
    if (!cfg.ffmpeg) {
      $("#ffmpeg-banner").classList.remove("hidden");
      const audioBtn = $("#audio-btn");
      audioBtn.disabled = true;
      audioBtn.title = I18N.t("needsffmpeg");
    }
  } catch (_) { /* se reintenta al refrescar */ }

  $("#cookies-select").addEventListener("change", (e) => {
    setCookiesBrowser(e.target.value).catch((err) => {
      showError($("#url-error"), err.message);
    });
  });
  $("#cookies-retry").addEventListener("click", () => analyze());
  $("#cookies-toggle").addEventListener("click", () => {
    state.cookiesOpen = true;
    renderCookies();
    $("#cookies-select").focus();
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
  // de idioma hay que repintar lo que ya esté en pantalla. La cola y el
  // historial se arreglan solos en el siguiente refresh().
  I18N.onChange(() => {
    // El bloque de cookies se repinta siempre (existe aunque no haya vídeo).
    // I18N ya ha devuelto la ayuda a su texto original en el idioma nuevo, así
    // que este es el momento de volver a guardarla como base.
    cookiesHelp.dataset.base = cookiesHelp.textContent;
    renderCookies();
    if (!state.info) return;
    // renderSubtitleOptions solo repuebla el select si cambia el vídeo; al
    // cambiar de idioma el vídeo es el mismo, así que hay que invalidarlo a
    // mano o el "(automático)" se quedaría en el idioma anterior.
    $("#sub-lang-select").dataset.url = "";
    renderPreview();
    renderSubtitleOptions();
    renderEdit();
  });

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
