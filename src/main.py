"Main initialization"
import os
import sys
from PySide6.QtWidgets import (QApplication) # pylint: disable=E0611

from utility import utils
from utility import thread
from dashboard.dashboard_ui import DashboardUI
from dashboard.dashboard_core import DashboardCore
from setting.announcement import Announcement
from setting.setting_ui import SettingUI


def main():
    "Main function"
    # Set theme for the program
    theme = utils.get_theme()

    if theme == "dark":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    elif theme == "light":
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

    app = QApplication(sys.argv)
    main_window = DashboardUI()
    announcement = Announcement()
    setting_ui = SettingUI()
    dashboad_core = DashboardCore()

    main_window.show()

    main_window.startup_worker = thread.Thread(main_window)
    # Connect signal from thread
    main_window.startup_worker.update_found.connect(
        lambda: setting_ui.update_messagebox(show_no_update_message=False))
    main_window.startup_worker.show_announcement.connect(
        lambda: announcement.show_announcement_window(main_window))
    main_window.startup_worker.ahk_not_installed.connect(
        lambda: dashboad_core.ahk_notinstalled_msg(main_window))
    main_window.startup_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
