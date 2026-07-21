"use strict";

const $ = (sel) => document.querySelector(sel);

const state = {
  info: null,
  mode: "video",
  subFormat: "txt",
  ffmpeg: false,
  // Edición del vídeo: recorte de duración (segundos), bordes (píxeles) y silenciado.
  edit: { start: 0, end: 0, duration: 0 },
};

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = "Error de red";
    try {
      const data = await res.json();
      if (data && data.detail) detail = String(data.detail);
    } catch (_) { /* respuesta sin JSON */ }
    throw new Error(detail);
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
  if (m >= 60) return `${Math.floor(m / 60)}h ${m % 60}m`;
  return `${m}:${String(s % 60).padStart(2, "0")} min`;
}

const STATUS_LABELS = {
  en_cola: "En cola",
  descargando: "Descargando...",
  procesando: "Procesando...",
  editando: "Editando...",
  completado: "Completado",
  error: "Error",
};

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

async function analyze(event) {
  event.preventDefault();
  const btn = $("#analyze-btn");
  const errorEl = $("#url-error");
  hideError(errorEl);
  btn.disabled = true;
  btn.textContent = "Analizando...";
  try {
    state.info = await post("/api/info", { url: $("#url-input").value });
    renderPreview();
  } catch (err) {
    $("#preview").classList.add("hidden");
    showError(errorEl, err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Analizar";
  }
}

function renderPreview() {
  const info = state.info;
  $("#preview-thumb").src = info.thumbnail || "";
  $("#preview-platform").textContent = info.platform || "Vídeo";
  $("#preview-title").textContent = info.title || info.url;
  const parts = [];
  if (info.uploader) parts.push(info.uploader);
  if (info.duration) parts.push(formatDuration(info.duration));
  $("#preview-sub").textContent = parts.join(" · ");
  renderQualityOptions();
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
  best.textContent = "Máxima disponible";
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

function renderSubtitleOptions() {
  const tracks = state.info?.subtitles || [];
  const select = $("#sub-lang-select");
  if (select.options.length !== tracks.length || select.dataset.url !== state.info?.url) {
    select.innerHTML = "";
    for (const t of tracks) {
      const opt = document.createElement("option");
      opt.value = t.code;
      opt.textContent = t.automatic ? `${t.name} (automático)` : t.name;
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
    showError($("#download-error"), "Este vídeo no tiene subtítulos disponibles");
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
  $("#trim-hint").textContent = duration ? `de ${formatTime(duration)}` : "";

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
      ? "El recorte deja el vídeo sin imagen"
      : `${info.width}x${info.height} queda en ${w}x${h}`;
    renderCropPreview(crop, info, bad);
  } else {
    result.textContent = "";
  }

  // Resumen en la cabecera plegable
  const parts = [];
  if (duration > 0 && (start > 0 || end < duration)) {
    parts.push(`${formatTime(start)}-${formatTime(end)}`);
  }
  if (crop.top || crop.bottom || crop.left || crop.right) parts.push("bordes");
  if ($("#mute-check").checked) parts.push("sin audio");
  const summary = $("#edit-summary");
  summary.textContent = parts.length ? parts.join(" · ") : "sin cambios";
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
    ? `(vídeo de ${info.width}x${info.height} px)`
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
  let statusText = STATUS_LABELS[job.status] || job.status;
  if (job.status === "descargando") {
    statusText = `${job.progress}%`;
    if (job.speed) statusText += ` · ${job.speed}`;
    if (job.eta) statusText += ` · ${job.eta}`;
  }
  status.textContent = statusText;
  head.append(title, status);
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
  const MODE_BADGES = { audio: "MP3", text: "TEXTO" };
  badge.textContent = MODE_BADGES[entry.mode] || entry.platform || "Vídeo";
  const title = document.createElement("span");
  title.className = "history-title";
  title.textContent = entry.title || entry.url;
  const date = document.createElement("span");
  date.className = "history-date";
  date.textContent = (entry.downloaded_at || "").replace("T", " ");
  head.append(badge, title, date);
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

  for (const btn of document.querySelectorAll("#mode-group button")) {
    btn.addEventListener("click", () => {
      state.mode = btn.dataset.mode;
      for (const b of document.querySelectorAll("#mode-group button")) {
        b.classList.toggle("active", b === btn);
      }
      renderQualityOptions();
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

  try {
    const cfg = await api("/api/config");
    $("#version").textContent = `v${cfg.version}`;
    $("#folder-input").value = cfg.default_folder;
    state.ffmpeg = cfg.ffmpeg;
    if (!cfg.ffmpeg) {
      $("#ffmpeg-banner").classList.remove("hidden");
      const audioBtn = $("#audio-btn");
      audioBtn.disabled = true;
      audioBtn.title = "Requiere FFmpeg";
    }
  } catch (_) { /* se reintenta al refrescar */ }

  for (const btn of document.querySelectorAll("#sub-format-group button")) {
    btn.addEventListener("click", () => {
      state.subFormat = btn.dataset.subfmt;
      for (const b of document.querySelectorAll("#sub-format-group button")) {
        b.classList.toggle("active", b === btn);
      }
    });
  }

  setupEdit();
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
  if (!info || !info.update_available) return;

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
      status.textContent = "Descargando la actualización... Expoal se reiniciará solo.";
      try {
        await api("/api/update/apply", { method: "POST" });
        status.textContent = "Instalando... la aplicación se cerrará en un momento.";
      } catch (err) {
        status.classList.add("err");
        status.textContent = err.message;
        btn.disabled = false;
      }
    });
  } else {
    // En modo web/navegador no hay instalador: el botón lleva a la descarga.
    btn.textContent = "Descargar";
    btn.addEventListener("click", () => {
      window.open(info.notes_url || "https://github.com/Mun1to/Expoal/releases/latest", "_blank");
    });
  }

  banner.classList.remove("hidden");
}

init();
