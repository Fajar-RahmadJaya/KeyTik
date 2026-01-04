import keyboard
import pynput
from PySide6.QtCore import QThread, Signal

from utility.diff import (Diff)


class Thread(QThread, Diff):
    finished = Signal()
    update_found = Signal(str)
    show_announcement = Signal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def run(self):
        self.main_window.initialize_exit_keys()

        latest_version = self.main_window.check_for_update()
        if latest_version:
            self.update_found.emit(latest_version)
        self.finished.emit()

        if self.main_window.announcement_condition:
            self.show_announcement.emit()

        if not hasattr(self.main_window, "keyboard_hook_initialized"):
            keyboard.hook(lambda event: self.main_window.multi_key_event(
                event, self.main_window.active_entry, None))
            self.main_window.mouse_listener = pynput.mouse.Listener(
                on_click=lambda *args: self.main_window.mouse_listening(*args)
            )
            self.main_window.mouse_listener.start()
            self.main_window.keyboard_hook_initialized = True