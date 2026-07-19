# Copyright 2024 Fajar Rahmad Jaya
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Key listening package."""

import keyboard
import pynput
from PySide6.QtCore import QEvent, QObject, QTimer, Signal  # pylint: disable=E0611
from PySide6.QtGui import QCursor  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QCheckBox,
    QLineEdit,
    QPushButton,
    QWidget,
)

from keytik.profile_mode.profile_mode_core import ProfileModeCore
from keytik.utility import constant


class KeyListening(QObject):
    """Listen to key press."""

    request_timer_start = Signal()

    def __init__(self, edit_frame):
        super().__init__()
        # Composition
        self.profile_mode_core = ProfileModeCore()

        # Signal
        self.request_timer_start.connect(self.profile_mode_core.release_timer)

        # Variable
        self.mouse_listening_initialized = False
        self.is_listening = False
        self.copas_rows = []

        # UI
        self.edit_frame: QWidget = edit_frame

    def eventFilter(self, _, event):  # pylint: disable=C0103
        """Filter event by key press and window."""
        if event.type() in (
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.FocusIn,
            QEvent.FocusOut,
        ):
            return True
        return event.type() in (
            QEvent.Close,
            QEvent.WindowDeactivate,
            QEvent.Hide,
            QEvent.Leave,
        )

    def toggle_other_buttons(self, target_button, other_button_enabled: bool):
        """Change the state of non selected button."""
        button_list = self.edit_frame.findChildren(QPushButton)
        for button in button_list:
            if button != target_button:
                button.setEnabled(other_button_enabled)

    def toggle_other_entry(self, target_entry, other_entry_enabled: bool):
        """Install or remove event filter to enable/disable entry."""
        entry_list = self.edit_frame.findChildren(QLineEdit)
        for entry in entry_list:
            if entry != target_entry:
                if other_entry_enabled:
                    entry.removeEventFilter(self)
                else:
                    entry.installEventFilter(self)

    def key_listening(self, target_entry, target_button):
        """Get and Listen to key press."""
        # Initialize mouse listening thread once
        if not self.mouse_listening_initialized:
            mouse_listener = pynput.mouse.Listener(on_click=self.mouse_listening)
            mouse_listener.start()
            self.mouse_listening_initialized = True

        if not self.is_listening:
            self.is_listening = True
            self.profile_mode_core.active_entry = target_entry
            self.profile_mode_core.pressed_keys = []
            self.profile_mode_core.last_combination = ""

            # Dsiable other entry
            self.toggle_other_entry(target_entry, other_entry_enabled=False)

            # Disbale other button
            self.toggle_other_buttons(target_button, other_button_enabled=False)

            self.profile_mode_core.set_timer = QTimer()
            self.profile_mode_core.set_timer.setSingleShot(True)
            self.profile_mode_core.set_timer.timeout.connect(
                lambda: self.profile_mode_core.finalize_combination(target_entry)
            )

            keyboard.hook(lambda event: self.multi_key_event(event, target_entry, target_button))

        else:
            self.is_listening = False
            self.profile_mode_core.active_entry = None
            self.profile_mode_core.pressed_keys = []

            # Enable other entry
            self.toggle_other_entry(target_entry, other_entry_enabled=True)

            # Enable other button
            self.toggle_other_buttons(target_button, other_button_enabled=True)

    def multi_key_event(self, event, entry_widget: QLineEdit, button):
        """Action when multiple key is pressed, set timer before saving the key."""
        if not self.is_listening or self.profile_mode_core.active_entry != entry_widget:
            return

        key = event.name
        sc_checkbox = self.edit_frame.findChild(QCheckBox, "ScanCodeCheckbox")

        if entry_widget.objectName() == "DefaultKeyEntry" and sc_checkbox.isChecked():
            key = f"SC{event.scan_code:02X}"

        if key.lower() in constant.changes_key:
            key = constant.changes_key[key.lower()]

        if len(key) == 1 and key.isupper() and key.isalpha():
            key = key.lower()

        if event.event_type == "down":
            if key not in self.profile_mode_core.pressed_keys:
                self.profile_mode_core.pressed_keys.append(key)
                self.profile_mode_core.update_widget(entry_widget)
            if hasattr(self, "release_timer") and self.profile_mode_core.set_timer.isActive():
                self.profile_mode_core.set_timer.stop()

        elif event.event_type == "up":
            if key in self.profile_mode_core.pressed_keys:
                self.profile_mode_core.pressed_keys.remove(key)
                if not self.profile_mode_core.pressed_keys:
                    self.key_listening(entry_widget, button)
                    self.request_timer_start.emit()

                elif hasattr(self, "release_timer"):
                    self.request_timer_start.emit()

    def mouse_listening(self, x, y, button, pressed):  # pylint: disable=W0613
        """Get and listen to mouse key press. Pynput on_click."""
        if not (self.is_listening and self.profile_mode_core.active_entry):
            return

        button_map = {
            pynput.mouse.Button.left: "Left Button",
            pynput.mouse.Button.right: "Right Button",
            pynput.mouse.Button.middle: "Middle Button",
        }
        mouse_button = button_map.get(button, getattr(button, "name", str(button)))

        if pressed and not self.check_mouse_event():
            if mouse_button not in self.profile_mode_core.pressed_keys:
                self.profile_mode_core.pressed_keys.append(mouse_button)
                self.profile_mode_core.update_widget(self.profile_mode_core.active_entry)
        elif mouse_button in self.profile_mode_core.pressed_keys:
            self.profile_mode_core.pressed_keys.remove(mouse_button)
            if not self.profile_mode_core.pressed_keys:
                self.key_listening(self.profile_mode_core.active_entry, None)
                self.request_timer_start.emit()

    def check_mouse_event(self):
        """Check if cursor is over any widget in key_rows."""
        local_pos = self.edit_frame.mapFromGlobal(QCursor.pos())
        widget = self.edit_frame.childAt(local_pos)
        return isinstance(widget, (QPushButton, QLineEdit, QCheckBox))
