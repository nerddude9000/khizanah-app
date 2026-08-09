import configparser
import os
import subprocess
import time

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from ui_mainwindow import Ui_MainWindow
from utils import resource_path
from ydl import DownloadType, DownloadWorker

IS_DEBUG = os.getenv("DEBUG", "false") == "true"
IS_LINUX = os.name == "posix"  # NOTE: macos isn't supported
CONFIG_PATH = "config.ini"
VERSION = "2.0.0 تجريبي"


class MainWindow(QMainWindow):
    is_downloading = False

    def __init__(self):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_app()

    def setup_app(self):
        self.ui.changePathButton.clicked.connect(lambda: self.update_download_path())
        self.ui.openPathButton.clicked.connect(lambda: self.open_download_path())
        self.ui.downloadButton.clicked.connect(lambda: self.start_download())
        self.ui.progressBar.hide()  # will get shown on first download
        self.ui.footerLabel.setText(
            f'<a href="https://github.com/nerddude9000/khizanah-app" style="white-space: pre-line; color: gray; text-decoration: none;">هذا التطبيق مجاني تماما. التزموا حدود الله في استخدامه.\nالإصدار {VERSION}</a>'
        )

        if not IS_DEBUG:
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

    def on_download_progress(self, d, is_playlist):
        status = d["status"]
        info = d["info_dict"]
        msg = self.ui.infoLabel.text()

        if status == "finished":
            # This does NOT mean that the entire download is finished, only fragments.
            pass

        elif status == "error":
            msg = "حدث خلل أثناء التحميل."

        elif status == "downloading":
            try:
                progress_percentage = round(
                    (d["downloaded_bytes"] / d["total_bytes"]) * 100
                )
                speed_bytes_per_sec = d.get("speed")
                eta = d.get("eta")

                self.ui.progressBar.setTextVisible(True)
                self.ui.progressBar.setValue(progress_percentage)

                if is_playlist:
                    current = info.get("playlist_index")
                    total = info.get("playlist_count")

                    msg = f"جاري تحميل القائمة... ({current} من {total})"
                else:
                    msg = "جاري التحميل..."

                if speed_bytes_per_sec:
                    speed_Mbytes_per_sec = round(
                        (float(speed_bytes_per_sec) / 1024) / 1024, 2
                    )
                    msg += f"  {speed_Mbytes_per_sec} مب/ث"

                if eta:
                    eta_str = time.strftime("%M:%S", time.gmtime(eta))
                    msg += f"  تبقى: {eta_str}"

            except:  # noqa: E722
                self.ui.progressBar.setTextVisible(False)
                self.ui.progressBar.setValue(0)
                msg = "جاري التحميل... (لم نستطع استخراج مدى اكتمال التحميل)."

            finally:
                if info.get("title"):
                    msg += f"\n{info.get("title")}"

        self.ui.infoLabel.setText(msg)

    def on_finish_download(self, err_code: int):
        self.ui.downloadButton.setDisabled(False)
        self.is_downloading = False

        if err_code:
            QMessageBox.critical(
                self,
                "هناك خلل",
                "حدث خلل أثناء التحميل.\nتأكدوا من الرابط الذي أدخلتموه، ومن الاتصال بالشبكة.\n\nوقد يكون الخلل من اليوتيوب، فانتظروا قليلا قبل إعادة المحاولة.",
            )
            self.ui.progressBar.setValue(0)
            self.ui.progressBar.setTextVisible(False)
            self.ui.infoLabel.setText("حدث خلل.")

        else:
            self.ui.infoLabel.setText("انتهى التحميل بنجاح.")
            self.ui.progressBar.setValue(100)
            QMessageBox.information(self, "تمت العملية بنجاح", "انتهى التحميل بنجاح.")

    def start_download(self):
        if self.is_downloading:
            return

        self.is_downloading = True
        url = self.ui.urlInput.text()

        if len(url) == 0:
            QMessageBox.question(
                self, "هناك خلل", "أدخلوا رابط المقطع أو قائمة التشغيل أولا."
            )
            return

        download_path = self.config.get("preferences", "download_path", fallback=None)

        if not download_path:
            QMessageBox.question(
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

        self.worker.progress_signal.connect(self.on_download_progress)
        self.worker.finish_signal.connect(self.on_finish_download)

        # Update UI before starting the worker
        self.ui.downloadButton.setDisabled(True)
        self.ui.progressBar.show()  # because it gets hidden at app startup
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
            QMessageBox.critical(
                self,
                "هناك خلل",
                "مجلد الخزانة الذي اخترتموه غير صحيح، قم بتغييره أولا.",
            )
            return

        if IS_LINUX:
            subprocess.Popen(["xdg-open", download_path])
        else:  # windows, no macos support
            os.startfile(download_path)

    def save_config(self):
        if IS_DEBUG:
            return

        with open("config.ini", "w", encoding="utf-8") as config_file:
            self.config.write(config_file)

    def load_config(self):
        if len(self.config.read(CONFIG_PATH, encoding="utf-8")) == 0:
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

    font_id = QFontDatabase.addApplicationFont(resource_path("assets/rubik.ttf"))
    family = QFontDatabase.applicationFontFamilies(font_id)[0]
    app.setFont(QFont(family, 14))

    window = MainWindow()
    window.show()

    app.exec()
