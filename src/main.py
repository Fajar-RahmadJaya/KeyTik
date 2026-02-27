import os
import sys
from PySide6.QtWidgets import (QApplication)

import utility.utils as utils
from ui.main_ui import MainUI
import utility.thread as thread


def main():
    if utils.theme == "dark":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    elif utils.theme == "light":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

    app = QApplication(sys.argv)
    main_window = MainUI()
    main_window.show()

    main_window.startup_worker = thread.Thread(main_window)
    main_window.startup_worker.update_found.connect(
        main_window.show_update_messagebox)
    main_window.startup_worker.show_announcement.connect(
        main_window.show_announcement_window)
    main_window.startup_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
