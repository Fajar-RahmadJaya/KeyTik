"Main initialization"
import os
import sys
from PySide6.QtWidgets import (QApplication) # pylint: disable=E0611

import utility.utils as utils
import utility.thread as thread
from dashboard.dashborad import Dashboard
from setting.announcement import Announcement
from utility.diff import Diff

def main():
    "Main function"
    if utils.theme == "dark":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    elif utils.theme == "light":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

    app = QApplication(sys.argv)
    main_window = Dashboard()
    announcement = Announcement()
    diff = Diff()

    main_window.show()

    main_window.startup_worker = thread.Thread(main_window)
    main_window.startup_worker.update_found.connect(
        diff.show_update_messagebox)
    main_window.startup_worker.show_announcement.connect(
        announcement.show_announcement_window)
    main_window.startup_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
