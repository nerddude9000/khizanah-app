import os
import subprocess

import PyInstaller.__main__

IS_LINUX = os.name == "posix"

if __name__ == "__main__":
    # first make sure the ui is synced with assets/gui.ui
    if IS_LINUX:
        subprocess.run(["sh", "./build_ui.sh"], check=True)
    else:
        subprocess.run(["build_ui.bat"], shell=True, check=True)

    # NOTE: see @FFMPEG comment in ydl.py
    ffmpeg_binary_path = "vendor/ffmpeg/linux/" if IS_LINUX else "vendor/ffmpeg/win64/"

    # TODO: try to not include unnecessary library files that bloat the executable (if possible).
    PyInstaller.__main__.run(
        [
            "main.py",
            "--onefile",
            "--noconsole",
            "--windowed",
            "--optimize",
            "2",
            "--name",
            "khizanah",
            "--icon",
            "./assets/icon.ico",
            "--add-data",
            "assets:assets",
            "--add-binary",
            f"{ffmpeg_binary_path}:{ffmpeg_binary_path}",
        ]
    )

    print("Done.")
