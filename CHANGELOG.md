# Changelog

All notable changes to Expoal. Dates are release dates; versions follow
[semantic versioning](https://semver.org/).

## [2.3.0] — 2026-07-31

### Added

- **See what it is doing.** A terminal panel, off by default and switched on from the header,
  showing the engine's real output live: which extractor ran, which format was picked, when it
  is merging. Copy it to a clipboard in one click when you need to report a problem.
- **Faster downloads.** A checkbox for concurrent fragments (built into yt-dlp, nothing to
  install), and another for [aria2c](https://aria2.github.io/) multi-connection downloads,
  enabled only when the binary is actually on your machine.
- **Pause and resume** a download in progress. What was already downloaded is kept, so
  resuming continues instead of starting over.
- **Retry failed downloads**, one by one or all at once. Failures are now recorded in the
  history too, so they survive a restart and can be retried days later.
- **Paste several links at once**: one per line, duplicates and junk lines removed before
  anything is queued, then pick which ones to download from the same checklist as playlists.
- **Cookies from a `cookies.txt` file**, as an alternative to reading them from the browser.
  This is the way out for Chrome and Edge on Windows, which encrypt their cookies since v127
  in a way yt-dlp cannot read.
- A test suite (`uv run pytest`) covering the option parsing, the queue state machine, the
  subtitle cleanup, the history and the log buffer.
- `THIRD_PARTY_NOTICES.md` and this changelog.

### Fixed

- Error messages no longer show raw terminal color codes (`ESC[0;31mERROR:`) in the queue
  and the history.
- FFmpeg is now also found next to the executable, not only on `PATH` and in winget's folder.

## [2.2.0] — 2026-07-24

- Playlists and channels: paste one and pick which videos to download from a checklist, all
  queued at once with a shared format, quality and folder. A video link that merely carries a
  `&list=` still downloads as a single video.

## [2.1.0] — 2026-07-23

- Use your browser's cookies for private, age-restricted and members-only videos, and for
  YouTube's bot checks. The app tells apart "you need to sign in" from "those cookies could
  not be read" and offers the fix where it fails.
- A field for raw yt-dlp options, in the same syntax as the official docs, validated on save.
- Checkboxes for the common wants: SponsorBlock, and embedding thumbnail, metadata, chapters
  and subtitles.

## [2.0.1] — 2026-07-21

- Translate the two editor strings that were still in Spanish with the app in English.

## [2.0.0] — 2026-07-21

- Cancel a download in progress, cleaning up the partial files it leaves behind.
- Clear finished jobs from the queue, and open a downloaded file's folder from the app.
- Updatable engine: yt-dlp refreshes itself between app releases, so downloads keep working
  when platforms change.

## [1.8.0] — 2026-07-21

- English interface alongside Spanish, in both the app and the landing page.

## [1.7.0] — 2026-07-21

- Choose the output format: MP4, MKV, MOV, WEBM for video; MP3, M4A, WAV, FLAC, OPUS for audio.

## [1.5.0] — 2026-07-21

- New Expoal logo and brand across app, installer and site.

## [1.4.0] — 2026-07-21

- Subtitle extraction: save the transcript as clean text or timed `.srt`, in any language the
  video offers, instead of or alongside the video.
- Self-update on Linux: the AppImage replaces itself.

## [1.3.0] — 2026-07-20

- Edit while you download: trim the length, crop the edges by pixels, strip the audio track.

## [1.2.0] — 2026-07-15

- Linux AppImage build published alongside the Windows release.

## [1.1.0] — 2026-07-07

- One-click self-update on Windows and automated releases from GitHub Actions.

## [1.0.0] — 2026-07-06

- First public release: paste a link, pick quality and folder, watch the queue, keep a history.
  Windows installer, MIT license and landing page.

[2.3.0]: https://github.com/Mun1to/Expoal/releases/tag/v2.3.0
[2.2.0]: https://github.com/Mun1to/Expoal/releases/tag/v2.2.0
[2.1.0]: https://github.com/Mun1to/Expoal/releases/tag/v2.1.0
[2.0.1]: https://github.com/Mun1to/Expoal/releases/tag/v2.0.1
[2.0.0]: https://github.com/Mun1to/Expoal/releases/tag/v2.0.0
[1.8.0]: https://github.com/Mun1to/Expoal/releases/tag/v1.8.0
[1.7.0]: https://github.com/Mun1to/Expoal/releases/tag/v1.7.0
[1.5.0]: https://github.com/Mun1to/Expoal/releases/tag/v1.5.0
[1.4.0]: https://github.com/Mun1to/Expoal/releases/tag/v1.4.0
[1.3.0]: https://github.com/Mun1to/Expoal/releases/tag/v1.3.0
[1.2.0]: https://github.com/Mun1to/Expoal/releases/tag/v1.2.0
[1.1.0]: https://github.com/Mun1to/Expoal/releases/tag/v1.1.0
[1.0.0]: https://github.com/Mun1to/Expoal/releases/tag/v1.0.0
