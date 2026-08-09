# This is a basic interface for ytdlp just to make things simpler
import os
from enum import Enum

import yt_dlp
from PySide6.QtCore import QThread, Signal
from yt_dlp import YoutubeDL

from utils import resource_path

DownloadType = Enum("DownloadType", ["m4a", "720p", "best"])
download_type_formats: dict[DownloadType, str] = {
    DownloadType["m4a"]: "139/ba/m4a",
    DownloadType["720p"]: "bv[height=720]+(139/ba/m4a)",
    DownloadType["best"]: "bv+ba",
}

#
# NOTE: if you're building this yourself, you are expected to provide
# linux and win64 binaries and put them into "./vendor/ffmpeg/<os>/".
# I can't push these into the repository as they exceed github's 100MB limit.
# I do however, Inshallah, bundle them into the release executables for ease of use.
#
FFMPEG_BINARY_PATH = resource_path(
    "vendor/ffmpeg/linux/" if os.name == "posix" else "vendor/ffmpeg/win64/"
)


#
# NOTE: This used to be a single sync function instead of a thread, which caused
# rendering to stop until the entire download finished or erred, which therefore
# progress elements to not show, and the app itself to freeze.
#
class DownloadWorker(QThread):
    progress_signal = Signal(dict, bool)
    finish_signal = Signal(int)
    is_playlist = False

    def __init__(
        self,
        url: str,
        download_type: DownloadType,
        download_path: str,
    ) -> None:
        super().__init__()

        # init the format variable based on passed type
        # refer to yt-dlp format docs for more information
        if download_type not in download_type_formats:
            raise ValueError  # should never happen

        dl_format = download_type_formats.get(download_type)

        self.options = {
            "url": url,
            "download_format": dl_format,
            "download_path": download_path,
        }

    def _extract_info(self):
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            info = ydl.extract_info(self.options["url"], download=False)

        return info

    def run(self):
        op = self.options
        template = "%(title)s.%(ext)s"

        try:
            info = self._extract_info()
            if bool(info.get("_type") == "playlist" or "entries" in info):
                template = "%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s"
                self.is_playlist = True
        except:  # noqa: E722
            self.finish_signal.emit(1)
            return

        with YoutubeDL(
            params={
                "format": op["download_format"],
                "outtmpl": os.path.join(op["download_path"], template),
                "progress_hooks": [self._hook],
                "ffmpeg_location": FFMPEG_BINARY_PATH,
                "ignoreerrors": (  # force stop when single video download fails, don't on playlists
                    "only_download" if self.is_playlist else False
                ),
            }
        ) as dl:
            try:
                error_code = dl.download([op["url"]])  # needs a list
                self.finish_signal.emit(error_code)
            except:  # noqa: E722
                self.finish_signal.emit(1)

    def _hook(self, data):
        self.progress_signal.emit(data, self.is_playlist)
