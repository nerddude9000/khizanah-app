# This is a basic interface for ytdlp just to make things simpler
from enum import Enum
from os import path

from yt_dlp import YoutubeDL

FFMPEG_BINARY_PATH = "./vendor/ffmpeg/ffmpeg"
DownloadType = Enum("DownloadType", ["m4a", "720p", "best"])

def download(url: str, download_type: DownloadType, download_location: str):
    if download_type == DownloadType["m4a"]:
        dl_format = "139/ba/m4a"
    elif download_type == DownloadType["720p"]:
        dl_format = "bv[height=720]+(139/ba/m4a)"
    else:
        dl_format = "bv+ba"
        
    with YoutubeDL(params={"format": dl_format, "outtmpl": path.join(download_location, "%(title)s%(ext)s")}) as dl:
        dl.download([url]) # needs a list

