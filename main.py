import os

from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from ui_mainwindow import Ui_MainWindow
from ydl import DownloadType, download

# TODO: The ui is too small, implement a real fix
os.environ["QT_SCALE_FACTOR"] = "1.5"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_app()

    def setup_app(self):
        # TODO: load download path from config file
        self.ui.pathButton.clicked.connect(lambda: self.update_download_path())

        self.ui.downloadButton.clicked.connect(lambda: self.start_download())

    def start_download(self):
        url = self.ui.urlInput.text()

        # TODO: maybe check with ytdlp?
        if len(url) == 0:
            QMessageBox.information(
                self, "هناك خلل", "أدخلوا رابط المقطع أو قائمة التشغيل أولا."
            )
            return

        download_location = self.ui.pathLabel.text()

        if not os.path.exists(download_location):
            QMessageBox.information(
                self,
                "هناك خلل",
                "مجلد الخزانة الذي اخترتموه غير صحيح، قم بتغييره أولا.",
            )
            return

        download_type: DownloadType

        if self.ui.downloadModeRadio_Audio.isChecked():
            download_type = DownloadType.m4a
        elif self.ui.downloadModeRadio_720p.isChecked():
            download_type = DownloadType["720p"]
        else:
            download_type = DownloadType.best

        download(url, download_type, download_location)

    def update_download_path(self):
        # TODO: save to a config file
        folder = QFileDialog.getExistingDirectory(self, "أين تريد تنزيل المقاطع؟")
        if folder:
            self.ui.pathLabel.setText(folder)


if __name__ == "__main__":
    app = QApplication()

    window = MainWindow()
    window.show()

    app.exec()
