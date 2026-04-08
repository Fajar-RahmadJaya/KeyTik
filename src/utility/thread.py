"Thread handler"

import keyboard
import pynput
from PySide6.QtCore import QThread, Signal  # pylint: disable=E0611

from utility.diff import (Diff)
from setting.announcement import Announcement
from setting.setting_core import SettingCore
from script_profile.write_script import WriteScript
from script_profile.profile_core import ProfileCore


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
        self.profile_core = ProfileCore()
        self.setting_core = SettingCore()

    def run(self):
        "Run check update on thread to increase dashborad initialization time"
        self.write_script.initialize_exit_keys()

        latest_version = self.setting_core.check_for_update()

        if latest_version:
            self.update_found.emit(latest_version)

        self.finished.emit()

        if self.announcement.load_announcement_condition():
            self.show_announcement.emit()

        if not hasattr(self.main_window, "keyboard_hook_initialized"):
            keyboard.hook(lambda event: self.profile_core.multi_key_event(
                event, self.main_window.active_entry, None))
            self.main_window.mouse_listener = pynput.mouse.Listener(
                 on_click=self.profile_core.mouse_listening
            )
            self.main_window.mouse_listener.start()
            self.main_window.keyboard_hook_initialized = True
