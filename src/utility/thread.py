"Thread handler"

import keyboard
from PySide6.QtCore import QThread, Signal  # pylint: disable=E0611

from setting.announcement import Announcement
from setting.setting_core import SettingCore
from script_profile.write_script import WriteScript


class Thread(QThread):
    "Thread at initializaion"
    update_found = Signal()
    show_announcement = Signal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def run(self):
        "Run check update on thread to increase dashborad initialization time"
        # To do: load all announcement file content on thread
        # when "show announcement" is true

        # Composition
        announcement = Announcement()
        write_script = WriteScript()
        setting_core = SettingCore()

        write_script.initialize_exit_keys()

        latest_version = setting_core.check_for_update()

        if latest_version:
            self.update_found.emit(latest_version)

        if announcement.load_announcement_condition():
            self.show_announcement.emit()

        def _dummy(_):
            pass

        dummy_hook = keyboard.hook(_dummy)
        keyboard.unhook(dummy_hook)
