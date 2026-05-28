"Main initialization"

import os
import sys
from PySide6.QtWidgets import QApplication  # pylint: disable=E0611

from keytik.utility import utils
from keytik.utility import thread
from keytik.utility import style
from keytik.dashboard.dashboard_ui import DashboardUI
from keytik.dashboard.dashboard_core import DashboardCore
from keytik.setting.announcement import Announcement
from keytik.setting.setting_ui import SettingUI


def main():
    "Main function"
    # Set Appearance
    config = utils.get_config()
    style_config = config.style
    theme = config.theme

    # Set normal dark and light theme
    if theme == "light" or style.IS_BASE_LIGHT:
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"
    elif theme == "dark" or not style.IS_BASE_LIGHT:
        os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"

    app = QApplication(sys.argv)
    app.setStyle(style_config)
    app.setPalette(style.PALETTE)
    # Set accent button highlight stylesheet
    app.setStyleSheet(style.button_highlight(style_sheet=True))

    main_window = DashboardUI()
    main_window.show()

    # Thread
    announcement = Announcement()
    setting_ui = SettingUI()
    dashboad_core = DashboardCore()

    main_window.startup_worker = thread.Thread(main_window)
    # Connect signal from thread
    main_window.startup_worker.update_found.connect(
        lambda: setting_ui.update_messagebox(show_no_update_message=False)
    )
    main_window.startup_worker.show_announcement.connect(
        lambda: announcement.show_announcement_window(main_window)
    )
    main_window.startup_worker.ahk_not_installed.connect(
        lambda: dashboad_core.ahk_notinstalled_msg(main_window)
    )
    main_window.startup_worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
