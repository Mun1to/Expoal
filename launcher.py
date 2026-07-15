"""PyInstaller entry point.

On Windows the packaged app opens its own native window. On Linux it opens in the
browser instead: pywebview there needs system WebKitGTK libraries that do not bundle
reliably across distros. Passing any argument falls through to the normal CLI.
"""
import multiprocessing
import sys

from expoal.__main__ import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if len(sys.argv) == 1 and sys.platform == "win32":
        sys.argv.append("--desktop")
    main()
