# Third-party notices

Expoal is MIT licensed (see [LICENSE](LICENSE)). The Windows installer, the portable
zip and the Linux AppImage bundle a Python runtime and the libraries below. This file
lists them, their licenses and where to get their source.

Versions are the ones resolved in [`uv.lock`](uv.lock) at build time; the exact set for
a given release is reproducible from that file.

## Bundled with the app

| Component | License | Source |
| --- | --- | --- |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | The Unlicense (public domain) | https://github.com/yt-dlp/yt-dlp |
| [FastAPI](https://github.com/fastapi/fastapi) | MIT | https://github.com/fastapi/fastapi |
| [Starlette](https://github.com/encode/starlette) | BSD-3-Clause | https://github.com/encode/starlette |
| [Pydantic](https://github.com/pydantic/pydantic) | MIT | https://github.com/pydantic/pydantic |
| [Uvicorn](https://github.com/encode/uvicorn) | BSD-3-Clause | https://github.com/encode/uvicorn |
| [pywebview](https://github.com/r0x0r/pywebview) | BSD-3-Clause | https://github.com/r0x0r/pywebview |
| [bottle](https://github.com/bottlepy/bottle) (via pywebview) | MIT | https://github.com/bottlepy/bottle |
| [platformdirs](https://github.com/tox-dev/platformdirs) | MIT | https://github.com/tox-dev/platformdirs |
| [h11](https://github.com/python-hyper/h11) | MIT | https://github.com/python-hyper/h11 |
| [anyio](https://github.com/agronholm/anyio) | MIT | https://github.com/agronholm/anyio |
| [click](https://github.com/pallets/click) | BSD-3-Clause | https://github.com/pallets/click |
| [CPython](https://github.com/python/cpython) | PSF License | https://github.com/python/cpython |

The engine updater downloads official **yt-dlp** wheels from PyPI at runtime, over HTTPS,
verified against the SHA-256 published by PyPI and restricted to `files.pythonhosted.org`.
Those wheels carry the same Unlicense terms as the bundled copy.

## Not bundled — used if you install them

These are **never** shipped with Expoal and never downloaded behind your back. Expoal only
looks for them on your `PATH`, next to its own executable, or in the winget package folder.

| Component | License | Source |
| --- | --- | --- |
| [FFmpeg](https://ffmpeg.org/) | LGPL-2.1+ / GPL-2+ depending on build | https://ffmpeg.org/download.html |
| [aria2](https://aria2.github.io/) | GPL-2.0-or-later (with OpenSSL exception) | https://github.com/aria2/aria2 |

Install FFmpeg with `winget install Gyan.FFmpeg`, and aria2 with `winget install aria2.aria2`
(or drop `aria2c.exe` next to `Expoal.exe`). If you ever redistribute a build of Expoal with
either binary included, you take on their license obligations, which are stricter than MIT.

## Fonts and assets

The interface uses the fonts already installed on your system (Segoe UI on Windows, the
system UI font elsewhere) and does not embed or download any web font. The logo and icons
are original work by Munir Torres and are covered by this repository's license.
