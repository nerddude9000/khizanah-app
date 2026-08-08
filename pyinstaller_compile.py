import os
import shutil

import PyInstaller.__main__

if __name__ == "__main__":
    PyInstaller.__main__.run(
        [
            "main.py",
            "--onefile",
            "--noconsole",
            "--windowed",
            "--icon",
            "./assets/icon.png",
        ]
    )

    print("compilation done, now moving necessary files to 'dist/'...")

    dist_vendor_path = (
        "./dist/vendor/ffmpeg/linux/"
        if os.name == "posix"
        else "./dist/vendor/ffmpeg/win64/"
    )

    print("moving ffmpeg binary")
    ffmpeg_binary_path = (
        "./vendor/ffmpeg/linux/ffmpeg"
        if os.name == "posix"
        else "./vendor/ffmpeg/win64/ffmpeg.exe"
    )

    os.makedirs(dist_vendor_path)
    shutil.copy(ffmpeg_binary_path, dist_vendor_path)

    print("Done.")
