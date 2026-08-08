import configparser
import os
import subprocess

from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from ui_mainwindow import Ui_MainWindow
from ydl import DownloadType, DownloadWorker

# TODO: The ui is too small, implement a real fix
os.environ["QT_SCALE_FACTOR"] = "1.5"
IS_DEBUG = os.getenv("DEBUG", "false")
IS_LINUX = os.name == "posix"  # macos isn't supported
CONFIG_PATH = "config.ini"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_app()

    def setup_app(self):
        # TODO: load download path from config file
        self.ui.changePathButton.clicked.connect(lambda: self.update_download_path())
        self.ui.openPathButton.clicked.connect(lambda: self.open_download_path())
        self.ui.downloadButton.clicked.connect(lambda: self.start_download())

        if IS_DEBUG == "false":
            self.load_config()

    def show_initial_load_popup(self):
        QMessageBox.information(
            self,
            "شروط الاستخدام",
            """أهلا بكم في تطبيق خزانة لتحميل المقاطع والصوتيات.

لا نحلّ لأحد استخدام هذا التطبيق في أي محذور شرعي، كتحميل الموسيقى أو مقاطع فيها تبرج أو البدع، إلا إذا كنتم ستحذفونها أو تردون عليها ونحو ذلك.
ولا يقتصر المحذور على ما ذكرنا، ويُُرجع فيه لأهل العلم من أهل السنة.

وفقنا الله وإياكم.""",
        )

    def on_progress_download(self, data):
        status = data["status"]

        # TODO: display different text for audio and video parts?
        if status == "finished":
            self.ui.infoLabel.setText("انتهى التحميل ناجحًا.")

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
            QMessageBox.information(self, "تمت العملية بنجاح", "تم تحميل المقطع بنجاح")

    def start_download(self):
        url = self.ui.urlInput.text()

        if len(url) == 0:
            QMessageBox.information(
                self, "هناك خلل", "أدخلوا رابط المقطع أو قائمة التشغيل أولا."
            )
            return

        download_path = self.config.get("preferences", "download_path", fallback=None)

        if not download_path:
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
            download_path,
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
        folder = QFileDialog.getExistingDirectory(self, "أين تريد تنزيل المقاطع؟")
        if folder:
            self.ui.pathLabel.setText(folder)
            self.config["preferences"] = {"download_path": folder}
            self.save_config()

    def open_download_path(self):
        download_path = self.config.get("preferences", "download_path", fallback=None)

        if not download_path:
            QMessageBox.information(
                self,
                "هناك خلل",
                "مجلد الخزانة الذي اخترتموه غير صحيح، قم بتغييره أولا.",
            )
            return

        if IS_LINUX:
            subprocess.Popen(["xdg-open", download_path])
        else:  # windows, no macos support
            subprocess.Popen(f'explorer "{download_path}"')

    def save_config(self):
        with open("config.ini", "w") as config_file:
            self.config.write(config_file)

    def load_config(self):
        if len(self.config.read(CONFIG_PATH)) == 0:
            # file doesn't exist (it should get created later in save_config)
            self.show_initial_load_popup()
            return

        loaded_download_path = self.config.get(
            "preferences", "download_path", fallback=None
        )

        if loaded_download_path:
            if not os.path.exists(loaded_download_path):
                #
                # if the path wasn't valid, set it to None here and now.
                # this is to prevent checking if the path is valid everytime it is used,
                # which is terrible for performance for something that shouldn't even happen.
                # so now -when using it- we will just check if it's None.
                #
                self.config.set("preferences", "download_path", None)
            else:
                self.ui.pathLabel.setText(loaded_download_path)


if __name__ == "__main__":
    app = QApplication()

    window = MainWindow()
    window.show()

    app.exec()
