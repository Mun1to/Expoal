<div align="center">

<img src="assets/icon-256.png" width="96" alt="Expoal">

# Expoal

**Paste a link from YouTube, TikTok or Instagram and get the video saved on your own disk.**

No third-party download sites, no ads, no uploads. Everything runs locally on your machine, powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp).

[![Download](https://img.shields.io/github/v/release/Mun1to/Expoal?label=download&style=for-the-badge&color=4E6CC8)](https://github.com/Mun1to/Expoal/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-E8B84B?style=for-the-badge)](LICENSE)
[![Website](https://img.shields.io/badge/website-expoal-4E6CC8?style=for-the-badge)](https://mun1to.github.io/Expoal/)

[**Website**](https://mun1to.github.io/Expoal/) · [**Download**](https://github.com/Mun1to/Expoal/releases/latest)

<img src="assets/screenshot-dark.png" width="820" alt="Expoal screenshot">

</div>

## Features

- Paste a link, preview the video and download it in the best available quality
- Choose the format: MP4 video or MP3 audio (audio extraction requires FFmpeg)
- Pick the resolution, and choose the destination folder with a native file browser
- Download queue with live progress, speed and ETA
- Persistent download history
- Light and dark theme with a toggle (remembers your choice, follows the system by default)
- Two ways to use it, same app:
  - Web mode: a local page in your browser
  - Desktop mode: a native window you can pin to the taskbar
- 100% local and private: the server only listens on 127.0.0.1, and your links and files never leave your computer

## Download

The easiest way: grab the latest `Expoal-windows.zip` from the [**releases page**](https://github.com/Mun1to/Expoal/releases/latest), unzip it anywhere and run `Expoal.exe`. It bundles Python and every dependency, so nothing else to install. Double-clicking opens the desktop window, which you can then pin to the taskbar.

> FFmpeg is not bundled (it is large). Install it for MP3 export and top-quality merges:
> `winget install Gyan.FFmpeg`

## Run from source

Requirements: Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Mun1to/Expoal.git
cd Expoal
uv sync

# Web mode: opens http://127.0.0.1:8710 in your browser
uv run expoal

# Desktop mode: opens a native window
uv run expoal --desktop
```

Options: `--port <n>` to change the web port, `--no-browser` to skip opening the browser.

### Build the standalone app yourself

```powershell
uv run pyinstaller --noconfirm --windowed --name Expoal --icon assets\expoal.ico --add-data "src\expoal\web;expoal\web" launcher.py
```

The result is in `dist\Expoal\Expoal.exe`.

## How it works

A small FastAPI server wraps yt-dlp and exposes a minimal API (`/api/info`, `/api/download`, `/api/pick-folder`, `/api/jobs`, `/api/history`). The same static web UI is served in your browser (web mode) or inside a pywebview native window (desktop mode). A local-origin guard blocks cross-origin requests, so no other site can talk to the server. Downloads run in a background queue, one at a time, and the history is stored as JSON in your user data folder.

## Legal notice

Download only content you own, content licensed for it, or content you have permission to save. Downloading media may violate the terms of service of some platforms. This tool is intended for personal archiving. You are responsible for how you use it.

## License

[MIT](LICENSE) © 2026 Munir Torres (Mun1to)
