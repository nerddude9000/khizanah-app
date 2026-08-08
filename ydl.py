# This is a basic interface for ytdlp just to make things simpler
import os
from enum import Enum

from PySide6.QtCore import QThread, Signal
from yt_dlp import YoutubeDL

DownloadType = Enum("DownloadType", ["m4a", "720p", "best"])

#
# NOTE: if you're building this yourself, you are expected to provide
# linux and win64 binaries and put them into "./vendor/ffmpeg/<os>/".
# I can't push these into the repository as they exceed github's 100MB limit.
# I do however, Inshallah, bundle them into the release executables for ease of use.
#
FFMPEG_BINARY_PATH = (
    "./vendor/ffmpeg/linux/" if os.name == "posix" else "./vendor/ffmpeg/win64/"
)


#
# NOTE: This used to be a single sync function instead of a thread, which caused
# rendering to stop until the entire download finished or erred, which therefore
# progress elements to not show, and the app itself to freeze.
#
class DownloadWorker(QThread):
    progress_signal = Signal(dict)
    finish_signal = Signal(int)

    def __init__(
        self,
        url: str,
        download_type: DownloadType,
        download_location: str,
    ) -> None:
        super().__init__()
        self.options = {
            "url": url,
            "download_type": download_type,
            "download_location": download_location,
        }

    # TODO: File path handling for playlists (such as creating a new folder for them)
    def run(self):
        op = self.options

        # init the format variable based on passed type
        # refer to yt-dlp format docs for more information
        if op["download_type"] == DownloadType["m4a"]:
            dl_format = "139/ba/m4a"
        elif op["download_type"] == DownloadType["720p"]:
            dl_format = "bv[height=720]+(139/ba/m4a)"
        elif op["download_type"] == DownloadType["best"]:
            dl_format = "bv+ba"
        else:
            raise AssertionError  # should never happen

        with YoutubeDL(
            params={
                "format": dl_format,
                "outtmpl": os.path.join(op["download_location"], "%(title)s.%(ext)s"),
                "progress_hooks": [self._hook],
                "ffmpeg_location": FFMPEG_BINARY_PATH,
            }
        ) as dl:
            try:
                error_code = dl.download([op["url"]])  # needs a list
                self.finish_signal.emit(error_code)
            except:  # noqa: E722
                self.finish_signal.emit(1)

    def _hook(self, data):
        self.progress_signal.emit(data)
