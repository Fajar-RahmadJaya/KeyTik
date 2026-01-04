import os
import sys
from PySide6.QtWidgets import (QApplication)

from utility.utils import (theme)
from logic.main_app import MainApp
from utility.thread import Thread


def main():
    if theme == "dark":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    elif theme == "light":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()

    main_window.startup_worker = Thread(main_window)
    main_window.startup_worker.update_found.connect(
        main_window.show_update_messagebox)
    main_window.startup_worker.show_announcement.connect(
        main_window.show_announcement_window)
    main_window.startup_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
