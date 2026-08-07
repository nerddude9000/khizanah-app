from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

def setup_events(window: MainWindow):
    window.ui.downloadButton.clicked.connect(
        lambda: QMessageBox.information(window, "Message", window.ui.urlInput.text())
    )

if __name__ == "__main__":
    app = QApplication()
    window = MainWindow()

    setup_events(window)

    window.show()
    app.exec()

