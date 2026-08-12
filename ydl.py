# This is a basic interface for ytdlp just to make things simpler
import os
from enum import Enum

import yt_dlp
from PySide6.QtCore import QThread, Signal
from yt_dlp import YoutubeDL
from yt_dlp.postprocessor.metadataparser import MetadataParserPP

from utils import resource_path

DownloadType = Enum("DownloadType", ["audio", "720p", "best"])
# refer to yt-dlp format docs for more information
download_type_formats: dict[DownloadType, str] = {
    DownloadType["audio"]: "139/ba/m4a",
    DownloadType["720p"]: "bv[height<=720]+(139/ba/m4a)",
    DownloadType["best"]: "bv+ba",
}

#
# @FFMPEG NOTE: if you're building this yourself, you are expected to provide
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
    progress_signal = Signal(dict, bool)  # progress_hooks_data, is_playlist
    finish_signal = Signal(int, bool)  # error_code, is_playlist
    is_playlist: bool = False

    def __init__(
        self,
        url: str,
        download_type: DownloadType,
        download_path: str,
        download_metadata: None | dict,
    ) -> None:
        super().__init__()
        self.options = {
            "url": url,
            "download_type": download_type,
            "download_path": download_path,
            "download_metadata": download_metadata,
        }

    def _extract_info(self):
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            info = ydl.extract_info(self.options["url"], download=False)

        return info

    def run(self):
        op = self.options

        try:
            # extract info to check some details, like if this is a playlist
            info = self._extract_info()
        except:  # noqa: E722
            # we probably don't want to continue if we couldn't even extract
            # info, so we just finish with an error.
            # and continuing without knowing if this is a playlist would be very bad for UX.
            self.finish_signal.emit(1, False)
            return

        template = "%(title)s.%(ext)s"
        if bool(info.get("_type") == "playlist" or "entries" in info):
            template = "%(playlist)s/%(title)s.%(ext)s"
            self.is_playlist = True

        metadata = op.get("download_metadata")
        # metadata gets added to audios exclusively, to save performance.
        # i don't see the benefit of adding it to video.
        if metadata and op["download_type"] == DownloadType["audio"]:
            postprocessors_for_metadata = [
                {
                    "key": "MetadataParser",
                    "actions": [],
                    "when": "pre_process",
                },
                {"key": "FFmpegMetadata", "add_metadata": True},
            ]

            if metadata.get("author"):
                postprocessors_for_metadata[0]["actions"].append(
                    (
                        MetadataParserPP.interpretter,
                        f"{metadata["author"]}",
                        "%(artist)s",
                    ),
                )

            if metadata.get("title"):
                postprocessors_for_metadata[0]["actions"].append(
                    (
                        MetadataParserPP.interpretter,
                        (
                            f"%(playlist_index)s - {metadata.get("title")}"
                            if self.is_playlist
                            else f"{metadata.get("title")}"
                        ),
                        "%(title)s",
                    ),
                )

        else:
            postprocessors_for_metadata = []

        dl_format = download_type_formats.get(op["download_type"])
        with YoutubeDL(
            params={
                "format": dl_format,
                "outtmpl": os.path.join(op["download_path"], template),
                "progress_hooks": [self._hook],
                "ffmpeg_location": FFMPEG_BINARY_PATH,
                "ignoreerrors": (  # force stop when single video download fails, don't on playlists
                    "only_download" if self.is_playlist else False
                ),
                "postprocessors": postprocessors_for_metadata,
                "concurrent_fragment_downloads": 4,
            }
        ) as dl:
            try:
                error_code = dl.download([op["url"]])  # needs a list
                self.finish_signal.emit(error_code, self.is_playlist)
            except:  # noqa: E722
                self.finish_signal.emit(1, self.is_playlist)

    def _hook(self, data):
        self.progress_signal.emit(data, self.is_playlist)
