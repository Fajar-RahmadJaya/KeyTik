"Thread handler"

import os
import keyboard
from PySide6.QtCore import QThread, Signal  # pylint: disable=E0611

from setting.setting_core import SettingCore
from script_profile.write_script import WriteScript
from utility import utils
from dashboard.dashboard_core import DashboardCore

class Thread(QThread):  # pylint: disable=R0903
    "Startup thread worker"
    update_found = Signal()
    show_announcement = Signal()
    ahk_not_installed = Signal()

    def run(self):
        "Run check update on thread to increase dashborad initialization time"
        # Composition
        write_script = WriteScript()
        setting_core = SettingCore()
        dashboard_core = DashboardCore()

        # Make sure all exit keys on script valid
        write_script.initialize_exit_keys()

        # Check for update
        latest_version = setting_core.check_for_update()
        if latest_version:
            self.update_found.emit()

        # Check whether AutoHotkey is installed
        if not os.path.exists(utils.ahkv2_dir):
            self.ahk_not_installed.emit()

        # Whether to show announcement or not
        if utils.get_config().show_announcement:
            self.show_announcement.emit()

        # Check AHI necessary file
        dashboard_core.check_ahi_dir()

        # Initialize keyboard hook thread once
        def _dummy(_):
            pass
        dummy_hook = keyboard.hook(_dummy)
        keyboard.unhook(dummy_hook)
