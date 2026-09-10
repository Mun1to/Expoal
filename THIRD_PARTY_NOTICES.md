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
| [curl_cffi](https://github.com/lexiforest/curl_cffi) | MIT | https://github.com/lexiforest/curl_cffi |
| [curl-impersonate](https://github.com/lexiforest/curl-impersonate) (linked into curl_cffi) | MIT, over [curl](https://curl.se/docs/copyright.html)'s MIT-like license | https://github.com/lexiforest/curl-impersonate |
| [cffi](https://github.com/python-cffi/cffi) | MIT-0 | https://github.com/python-cffi/cffi |
| [pycparser](https://github.com/eliben/pycparser) | BSD-3-Clause | https://github.com/eliben/pycparser |
| [certifi](https://github.com/certifi/python-certifi) | MPL-2.0 | https://github.com/certifi/python-certifi |
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

**Why curl_cffi is in that list.** yt-dlp's TikTok and Instagram extractors ask to present a
real browser's TLS handshake; without it those sites answer some requests with a filler page
instead of the video. `curl_cffi` is what yt-dlp itself documents for this, and it is requested
through yt-dlp's own `curl-cffi` extra so that yt-dlp pins the versions it supports. It changes
how a request looks, nothing else: Expoal still asks for one page per click, sends nothing but
the link you pasted, and keeps no data about anyone.

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
