import os
import keyboard
import ctypes
import time
from pynput import mouse
from PySide6.QtWidgets import (QMessageBox)
from PySide6.QtCore import QTimer, Signal, QObject, QEvent
from utility.constant import (interception_install_path)


class InputBlocker(QObject):
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
                            QEvent.KeyPress, QEvent.KeyRelease,
                            QEvent.FocusIn, QEvent.FocusOut):
            return True
        if event.type() in (QEvent.Close, QEvent.WindowDeactivate,
                            QEvent.Hide, QEvent.Leave):
            return True
        return False


class EditScriptLogic(QObject):
    request_timer_start = Signal(object)

    def __init__(self):
        super().__init__()
        self.request_timer_start.connect(self.release_timer)

    def check_interception_driver(self):
        driver_path = r"C:\Windows\System32\drivers\keyboard.sys"

        if os.path.exists(driver_path):
            return True
        else:
            reply = QMessageBox.question(
                None,
                "Driver Not Found",
                "Interception driver is not installed. This driver is required to use assign on specific device feature.\n \n \nNote: Restart your device after installation.\n" # noqa
                "Would you like to install it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if os.path.exists(interception_install_path):

                        install_dir = (os.path.dirname
                                       (interception_install_path))

                        ctypes.windll.shell32.ShellExecuteW(
                            None,
                            "runas",
                            "cmd.exe",
                            f"/k cd /d {install_dir} && {os.path.basename(interception_install_path)}", # noqa
                            None,
                            1
                        )
                    else:
                        QMessageBox.critical(
                            None,
                            "Installation Failed",
                            "Installation script not found. Please check your installation." # noqa
                        )
                except Exception as e:
                    QMessageBox.critical(None, "Error", f"An error occurred during installation: {str(e)}") # noqa
            return False

    def update_entry(self):
        shortcut_combination = '+'.join(self.pressed_keys)
        if hasattr(self, "active_entry") and self.active_entry is not None:
            self.active_entry.setText(shortcut_combination)

    def get_script_name(self):
        script_name = self.script_name_entry.text().strip()
        if not script_name:
            QMessageBox.warning(None, "Input Error", "Please enter a Profile name.") # noqa
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name

    def is_widget_valid(self, widget_tuple):
        try:
            entry_widget, button_widget = widget_tuple
            return entry_widget is not None and button_widget is not None
        except Exception:
            return False

    def key_listening(self, entry_widget, button):
        def toggle_other_buttons(state):
            if hasattr(self, 'key_rows'):
                for key_row in self.key_rows:
                    (_, _, orig_button, remap_button, _, _, _) = key_row

                    if orig_button != button and orig_button is not None:
                        orig_button.setEnabled(state)
                    if remap_button != button and remap_button is not None:
                        remap_button.setEnabled(state)

            if hasattr(self, 'copas_rows'):
                for copas_row in self.copas_rows:
                    (_, _, copy_button, paste_button, _, _) = copas_row

                    if copy_button != button and copy_button is not None:
                        copy_button.setEnabled(state)
                    if paste_button != button and paste_button is not None:
                        paste_button.setEnabled(state)

            for _, shortcut_button in self.shortcut_rows:
                if shortcut_button != button and shortcut_button is not None:
                    shortcut_button.setEnabled(state)

        if not self.is_listening:

            self.is_listening = True
            self.active_entry = entry_widget
            self.previous_button_text = button.text()

            self.use_scan_code = False
            if hasattr(self, 'key_rows'):
                for key_row in self.key_rows:
                    (orig_entry, remap_entry, orig_button, _, _, _,
                     hold_interval_entry) = key_row

                    if button == orig_button:
                        parent_widget = button.parent()
                        if parent_widget:
                            sc_checkboxes = [child for child
                                             in parent_widget.
                                             findChildren(QObject)
                                             if child.objectName() ==
                                             "sc_checkbox"]
                            if sc_checkboxes:
                                self.use_scan_code = (
                                    sc_checkboxes[0].isChecked())
                            break

            entries_to_disable = []
            if hasattr(self, 'script_name_entry'):
                entries_to_disable.append((self.script_name_entry, None))
            if hasattr(self, 'keyboard_entry'):
                entries_to_disable.append((self.keyboard_entry, None))
            if hasattr(self, 'program_entry'):
                entries_to_disable.append((self.program_entry, None))

            if hasattr(self, 'key_rows'):
                for key_row in self.key_rows:
                    (
                        orig_entry, remap_entry, _, _, _, _,
                        hold_interval_entry
                    ) = key_row
                    entries_to_disable.append((orig_entry, None))
                    entries_to_disable.append((remap_entry, None))
                    entries_to_disable.append((hold_interval_entry, None))

            if hasattr(self, 'shortcut_rows'):
                for shortcut_entry, _ in self.shortcut_rows:
                    entries_to_disable.append((shortcut_entry, None))

            if hasattr(self, 'copas_rows'):
                for copas_row in self.copas_rows:
                    copy_entry, paste_entry, _, _, _, _ = copas_row
                    entries_to_disable.append((copy_entry, None))
                    entries_to_disable.append((paste_entry, None))

            self.disable_input(entries_to_disable)

            if hasattr(self, "edit_window"):
                if not hasattr(self, "_window_blocker"):
                    self._window_blocker = InputBlocker()
                self.edit_window.installEventFilter(self._window_blocker)

            self.ignore_next_click = True
            toggle_other_buttons(False)

            button.clicked.disconnect()
            button.clicked.connect(lambda: self.key_listening
                                   (entry_widget, button))

            self.currently_pressed_keys = []
            self.last_combination = ""
            self.release_timer = QTimer()
            self.release_timer.setSingleShot(True)
            self.release_timer.timeout.connect(lambda:
                                               self.finalize_combination
                                               (entry_widget))
            keyboard.hook(lambda event: self.multi_key_event
                          (event, entry_widget, button))

        else:
            self.is_listening = False
            self.active_entry = None

            entries_to_enable = []
            if hasattr(self, 'script_name_entry'):
                entries_to_enable.append((self.script_name_entry, None))

            if hasattr(self, 'keyboard_entry'):
                entries_to_enable.append((self.keyboard_entry, None))

            if hasattr(self, 'program_entry'):
                entries_to_enable.append((self.program_entry, None))

            if hasattr(self, 'key_rows'):
                for key_row in self.key_rows:
                    (
                        orig_entry, remap_entry, _, _, _, _,
                        hold_interval_entry
                    ) = key_row
                    entries_to_enable.append((orig_entry, None))
                    entries_to_enable.append((remap_entry, None))
                    entries_to_enable.append((hold_interval_entry, None))

            if hasattr(self, 'shortcut_rows'):
                for shortcut_entry, _ in self.shortcut_rows:
                    entries_to_enable.append((shortcut_entry, None))

            if hasattr(self, 'copas_rows'):
                for copas_row in self.copas_rows:
                    copy_entry, paste_entry, _, _, _, _ = copas_row
                    entries_to_enable.append((copy_entry, None))
                    entries_to_enable.append((paste_entry, None))

            self.enable_input(entries_to_enable)
            toggle_other_buttons(True)

            if hasattr(self, "edit_window") and hasattr(
                    self, "_window_blocker"):
                self.edit_window.removeEventFilter(self._window_blocker)

            if button is not None:
                button.clicked.disconnect()
                button.clicked.connect(lambda: self.key_listening
                                       (entry_widget, button))

    def multi_key_event(self, event, entry_widget, button):
        if not self.is_listening or self.active_entry != entry_widget:
            return

        if hasattr(self, 'use_scan_code') and self.use_scan_code:
            key = f"SC{event.scan_code:02X}"
        else:
            key = event.name

        if (len(key) == 1 and key.isupper() and key.isalpha()):
            key = key.lower()

        if event.event_type == "down":
            if key not in self.currently_pressed_keys:
                self.currently_pressed_keys.append(key)
                self.update_widget(entry_widget)
            if (hasattr(self, "release_timer")
                    and self.release_timer.isActive()):
                self.release_timer.stop()

        elif event.event_type == "up":
            if key in self.currently_pressed_keys:
                self.currently_pressed_keys.remove(key)
                if not self.currently_pressed_keys:
                    self.key_listening(entry_widget, button)
                    self.request_timer_start.emit(entry_widget)

                else:
                    if hasattr(self, "release_timer"):
                        self.request_timer_start.emit(entry_widget)

    def mouse_listening(self, x, y, button, pressed):
        if self.is_listening and self.active_entry:
            if pressed:
                if self.ignore_next_click and button == mouse.Button.left:
                    self.ignore_next_click = False
                    return

                if button == mouse.Button.left:
                    mouse_button = "Left Button"
                elif button == mouse.Button.right:
                    mouse_button = "Right Button"
                elif button == mouse.Button.middle:
                    mouse_button = "Middle Button"
                else:
                    mouse_button = button.name

                current_time = time.time()

                if current_time - self.last_key_time > self.timeout:
                    self.pressed_keys = []

                if mouse_button not in self.pressed_keys:
                    self.pressed_keys.append(mouse_button)
                    self.update_entry()

                self.last_key_time = current_time

            else:
                if button == mouse.Button.left:
                    mouse_button = "Left Button"
                elif button == mouse.Button.right:
                    mouse_button = "Right Button"
                elif button == mouse.Button.middle:
                    mouse_button = "Middle Button"
                else:
                    mouse_button = button.name

                if mouse_button in self.pressed_keys:
                    self.pressed_keys.remove(mouse_button)
                    if not self.pressed_keys:
                        self.key_listening(self.active_entry, None)
                        self.request_timer_start.emit(self.active_entry)
                    else:
                        if hasattr(self, "release_timer"):
                            self.request_timer_start.emit(self.active_entry)

    def release_timer(self, entry_widget):
        if hasattr(self, "release_timer"):
            self.release_timer.start(400)

    def format_key_combo(self, keys):
        def format_key(k):
            if len(k) == 1 and k.islower():
                return k
            return k[:1].upper() + k[1:] if k else k

        if isinstance(keys, (list, set)):
            keys = list(keys)
        if len(keys) == 1:
            return format_key(keys[0])
        return ' + '.join(format_key(k) for k in keys)

    def update_widget(self, entry_widget):
        combo = self.format_key_combo(self.currently_pressed_keys)
        entry_widget.setText(combo)
        self.last_combination = combo

    def finalize_combination(self, entry_widget):
        entry_widget.setText(self.last_combination)
        self.currently_pressed_keys = set()

    def disable_input(self, entry_rows):
        if not hasattr(self, "_input_blocker"):
            self._input_blocker = InputBlocker()
        for entry_tuple in entry_rows:
            entry = entry_tuple[0]
            if entry is not None:
                entry.installEventFilter(self._input_blocker)

    def enable_input(self, entry_rows):
        if hasattr(self, "_input_blocker"):
            for entry_tuple in entry_rows:
                entry = entry_tuple[0]
                if entry is not None:
                    entry.removeEventFilter(self._input_blocker)

    def replace_raw_keys(self, key, key_map):
        return key_map.get(key, key)
