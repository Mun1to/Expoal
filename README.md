# Expoal

Paste a link from YouTube, TikTok or Instagram and get the video saved on your own disk.

No third-party download sites, no ads, no uploads. Everything runs locally on your machine, powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp).

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

## Requirements

- Python 3.10+ and [uv](https://docs.astral.sh/uv/)
- FFmpeg (recommended): needed for MP3 extraction and for merging the highest video qualities
  - Windows: `winget install Gyan.FFmpeg` (Expoal finds it even before you restart the terminal)

## Getting started

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

## Standalone app (Windows)

You can build a single `Expoal.exe` that bundles Python and every dependency, so it runs
without installing anything. Double-clicking it opens the desktop window; you can then pin it
to the taskbar.

```powershell
uv run pyinstaller --noconfirm --windowed --name Expoal --icon assets\expoal.ico --add-data "src\expoal\web;expoal\web" launcher.py
```

The result is in `dist\Expoal\Expoal.exe`. (FFmpeg is not bundled: install it separately for
MP3 and top-quality merges.)

## How it works

A small FastAPI server wraps yt-dlp and exposes a minimal API (`/api/info`, `/api/download`, `/api/jobs`, `/api/history`). The same static web UI is served in your browser (web mode) or inside a pywebview native window (desktop mode). Downloads run in a background queue, one at a time, and the history is stored as JSON in your user data folder.

## Legal notice

Download only content you own, content licensed for it, or content you have permission to save. Downloading media may violate the terms of service of some platforms. This tool is intended for personal archiving. You are responsible for how you use it.

## License

MIT
