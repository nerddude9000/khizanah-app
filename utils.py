import os
import sys


# Source - https://stackoverflow.com/a/13790741
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except:  # noqa: E722
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# also works for B/s to MB/s
def bytes_to_mega_bytes(n: float, ndigits: int = 2) -> float:
    n = float(n)  # convert just in case
    return round((n / 1024) / 1024, ndigits)
