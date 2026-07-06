"""PyInstaller entry point: Expoal.exe opens the desktop window by default.

Passing any argument (e.g. --port/--no-browser) falls through to the normal CLI.
"""
import multiprocessing
import sys

from expoal.__main__ import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if len(sys.argv) == 1:
        sys.argv.append("--desktop")
    main()
