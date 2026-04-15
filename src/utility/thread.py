"Thread handler"

import keyboard
from PySide6.QtCore import QThread, Signal  # pylint: disable=E0611

from utility.diff import (Diff)
from setting.announcement import Announcement
from setting.setting_core import SettingCore
from script_profile.write_script import WriteScript


class Thread(QThread, Diff):
    "Thread at initializaion"
    finished = Signal()
    update_found = Signal()
    show_announcement = Signal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.announcement = Announcement()
        self.write_script = WriteScript()
        self.setting_core = SettingCore()

    def run(self):
        "Run check update on thread to increase dashborad initialization time"
        self.write_script.initialize_exit_keys()
        # To do: load all announcement file content on thread
        # when "show announcement" is true

        latest_version = self.setting_core.check_for_update()

        if latest_version:
            self.update_found.emit(latest_version)

        self.finished.emit()

        if self.announcement.load_announcement_condition():
            self.show_announcement.emit()

        def _dummy(_):
            pass

        dummy_hook = keyboard.hook(_dummy)
        keyboard.unhook(dummy_hook)
