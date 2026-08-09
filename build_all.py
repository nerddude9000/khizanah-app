import os
import shutil
import subprocess

import PyInstaller.__main__

IS_LINUX = os.name == "posix"

if __name__ == "__main__":
    # first, make sure the ui is synced with assets/gui.ui
    if IS_LINUX:
        subprocess.run(["sh", "./build_ui.sh"], shell=True, check=True)
    else:
        subprocess.run(["./build_ui.bat"], shell=True, check=True)

    PyInstaller.__main__.run(
        [
            "main.py",
            "--onefile",
            "--noconsole",
            "--windowed",
            "--icon",
            "./assets/icon.ico",
        ]
    )

    print("compilation done, now moving necessary files to 'dist/'...")

    dist_vendor_path = (
        "./dist/vendor/ffmpeg/linux/" if IS_LINUX else "./dist/vendor/ffmpeg/win64/"
    )

    print("moving ffmpeg binary to dist/")

    ffmpeg_binary_path = (
        "./vendor/ffmpeg/linux/ffmpeg"
        if IS_LINUX
        else "./vendor/ffmpeg/win64/ffmpeg.exe"
    )

    os.makedirs(dist_vendor_path, exist_ok=True)
    shutil.copy(ffmpeg_binary_path, dist_vendor_path)

    print("Done.")
