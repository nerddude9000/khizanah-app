import os

from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from ui_mainwindow import Ui_MainWindow
from ydl import DownloadType, DownloadWorker

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

    def on_progress_download(self, data):
        status = data["status"]

        # TODO: display different text for audio and video parts?
        if status == "finished":
            self.ui.infoLabel.setText("انتهى التحميل.")
        elif status == "error":
            self.ui.infoLabel.setText("حدث خلل أثناء التحميل.")
        elif status == "downloading":
            try:
                progress_percentage = round(
                    (data["downloaded_bytes"] / data["total_bytes"]) * 100
                )

                self.ui.progressBar.setTextVisible(True)
                self.ui.progressBar.setValue(progress_percentage)
                self.ui.infoLabel.setText("جاري التحميل...")
            except:  # noqa: E722
                self.ui.progressBar.setTextVisible(False)
                self.ui.progressBar.setValue(0)
                self.ui.infoLabel.setText(
                    "جاري التحميل... (لم نستطع استخراج مدى اكتمال التحميل)."
                )

    def on_finish_download(self, err_code: int):
        self.ui.downloadButton.setDisabled(False)
        self.ui.progressBar.setTextVisible(False)

        if err_code:
            QMessageBox.information(
                self,
                "هناك خلل",
                f"حدث خلل أثناء التحميل ({err_code})\nتأكدوا من الرابط الذي أدخلتموه، ومن الاتصال بالشبكة.",
            )
            self.ui.progressBar.setValue(0)
        else:
            # TODO: Add button for opening the containing folder
            QMessageBox.information(self, "تمت العملية بنجاح", "تم تحميل المقطع بنجاح")

    def start_download(self):
        url = self.ui.urlInput.text()

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

        # Set download_type based on selected ui radio
        download_type: DownloadType
        if self.ui.downloadModeRadio_Audio.isChecked():
            download_type = DownloadType.m4a
        elif self.ui.downloadModeRadio_720p.isChecked():
            download_type = DownloadType["720p"]
        else:
            download_type = DownloadType.best

        # We must use self to prevent it from being garbage collected
        self.worker = DownloadWorker(
            url,
            download_type,
            download_location,
        )
        self.worker.progress_signal.connect(self.on_progress_download)
        self.worker.finish_signal.connect(self.on_finish_download)

        # Update UI before starting the worker
        self.ui.downloadButton.setDisabled(True)
        self.ui.progressBar.setValue(0)
        self.ui.progressBar.setTextVisible(True)
        self.ui.infoLabel.setText("انتظروا قليلا حتى يبدأ التحميل...")

        self.worker.start()

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
