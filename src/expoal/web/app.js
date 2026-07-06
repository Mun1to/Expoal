"use strict";

const $ = (sel) => document.querySelector(sel);

const state = {
  info: null,
  mode: "video",
  ffmpeg: false,
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
  completado: "Completado",
  error: "Error",
};

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
  hideError($("#download-error"));
  $("#preview").classList.remove("hidden");
}

function renderQualityOptions() {
  const select = $("#quality-select");
  select.innerHTML = "";
  select.disabled = state.mode === "audio";
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
  badge.textContent = entry.mode === "audio" ? "MP3" : (entry.platform || "Vídeo");
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

  refresh();
  setInterval(refresh, 1500);
}

init();
