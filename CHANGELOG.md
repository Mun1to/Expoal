# Changelog

All notable changes to Expoal. Dates are release dates; versions follow
[semantic versioning](https://semver.org/).

## [2.5.3] — 2026-08-19

### Added

- **Every quality now says what it weighs.** "Best available" on a twelve-hour video is 114 GB,
  and nothing on screen said so: you picked it thinking of an ordinary video and found out half
  an hour later. The dropdown now reads "2160p — 8.4 GB". The figure is not a guess: each
  quality asks yt-dlp itself, using the very selector the download will use, and adds up the
  video and audio tracks. It costs no extra request.
- **Clips carry their time range in the file name.** A clip used to overwrite the full video it
  came from, silently. It now saves as `Title [id] 1m00s-1m30s.mp4`, so the original survives
  and two clips of the same video can live side by side.

### Fixed

- **Downloads no longer die on "come back in a minute".** A 429 (you are going too fast) or a
  5xx (the server is having a moment) counted as a permanent failure, so a download stopped
  dead where waiting twenty seconds would have been enough. Both are now retried.
- **The engine no longer deletes itself.** Expoal wiped its downloaded yt-dlp whenever the app
  version did not match the one that fetched it, which meant two installations sharing the same
  folder destroyed each other's engine on every start, and a long video would then fail again.
- **YouTube's storyboards are gone from the quality list.** 27p, 45p and 90p are the thumbnail
  strips of the seek bar, not video: picking one always failed with "Requested format is not
  available".
- **Big downloads survive expiring links.** A long download keeps asking for a fresh address as
  it advances, instead of giving up after a fixed number of tries on a link that has already
  expired. Measured on a 12-hour video: 1.47 GB straight through, past the point where it used
  to die.
- **The engine updater reaches yt-dlp's nightly builds.** It only looked at the last stable
  release, so when YouTube broke that build the fix was out of reach behind the very button
  meant to deliver it.

## [2.5.2] — 2026-08-17

### Fixed

- **"Open folder" opens the folder again.** With a space anywhere in the file name, and video
  titles are full of them, Windows Explorer quietly opened Documents instead of selecting the
  file. It gave no error, so from the code working and not working looked identical.

## [2.5.1] — 2026-08-17

### Added

- **The destination folder is remembered.** Where your videos go is a preference, not a
  decision to retype on every start.

### Fixed

- **Clipping works on 4K videos.** The shortcut that downloads only the part you asked for
  never ran on modern video, because YouTube pairs it with audio in a container that carries no
  fragment table, and one track without it was enough to discard the shortcut entirely.
  Measured on a ten-hour video trimmed to one minute: 73 MB in four seconds, against 32.7 GB in
  twenty minutes. When the shortcut cannot run, the terminal panel now says why.
- **A byte-order mark no longer empties your history.** A stray marker at the start of the file,
  which any Windows editor can leave behind, made the history read as empty, and the next
  download overwrote it.

## [2.5.0] — 2026-08-14

### Added

- **Trim audio too, not just video.** Keeping one minute of a three-hour interview is as
  ordinary in MP3 as it is in video, and the editor used to disappear the moment you picked
  audio. It now stays, showing only the duration.
- **Concurrent fragments are on by default.** It is built into yt-dlp, needs nothing installed
  and leaves the resulting file untouched, so the cheapest speed-up there is no longer hides
  behind a checkbox. Existing installations get it once on the next start.

### Fixed

- Switching between Spanish and English no longer wipes the trim you had marked and closes the
  editor in your face.

## [2.4.0] — 2026-08-14

### Added

- **Trimming downloads only the part you asked for.** Cutting one minute out of a three-hour
  video used to download all three hours first. Expoal now reads the fragment table that
  streaming video carries, works out which bytes hold those minutes, and asks for those alone:
  measured on a real video, 4% of the file and three seconds against thirteen minutes. Where the
  site does not allow it, the whole video is downloaded and trimmed afterwards, as before, and
  the result is identical either way.

### Fixed

- **A hiccup in the connection no longer kills the download.** The ten retries yt-dlp is known
  for are its command line's defaults; used as a library it was doing none, so a single timeout
  or an expired link threw away a download that was nearly finished. Files are now fetched in
  chunks, so a failure costs one chunk, and a network error retries the job with fresh links,
  keeping what had already been downloaded.

## [2.3.1] — 2026-08-13

### Fixed

- **The cookies box stopped fighting you.** It reappeared every second and a half after a
  failed download, could not be closed once a browser was picked, closed its own dropdown
  while you were using it, and lost the row where you were typing the path to a
  `cookies.txt` if you cancelled the file picker. It now has a close button, closes with
  Escape, and once closed the link tells you which cookies are in use.
- **The queue and the history are only redrawn when they change.** Rebuilding them on every
  poll made the "that file is gone" warning on the folder button vanish before it could be
  read, and dropped keyboard focus out of the row buttons.
- A paused download no longer advertises the speed and time left it had before it stopped.
- A video with no thumbnail no longer leaves a broken image in its place.
- Subtitles are preselected in the language the app is set to, instead of always Spanish.

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

[2.5.0]: https://github.com/Mun1to/Expoal/releases/tag/v2.5.0
[2.4.0]: https://github.com/Mun1to/Expoal/releases/tag/v2.4.0
[2.3.1]: https://github.com/Mun1to/Expoal/releases/tag/v2.3.1
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
