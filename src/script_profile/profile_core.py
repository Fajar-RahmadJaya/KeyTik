"Logic for create/edit profile"

import json
import keyboard
from pynput import mouse

from PySide6.QtWidgets import (QMessageBox, QPushButton)  # pylint: disable=E0611
from PySide6.QtCore import QTimer, Signal, QObject, QEvent  # pylint: disable=E0611

from utility import constant



class InputBlocker(QObject):
    "Input blocker"
    def event_filter(self, _, event):
        "Filter event by key press and window"
        if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease,
                            QEvent.KeyPress, QEvent.KeyRelease,
                            QEvent.FocusIn, QEvent.FocusOut):
            return True
        if event.type() in (QEvent.Close, QEvent.WindowDeactivate,
                            QEvent.Hide, QEvent.Leave):
            return True
        return False


class ProfileCore(QObject):
    "Create/edit profile logic"
    request_timer_start = Signal(object)

    def __init__(self):
        super().__init__()
        self.request_timer_start.connect(self.release_timer)

        self.is_listening = False
        self.use_scan_code = False
        self._window_blocker = InputBlocker()
        self._input_blocker = InputBlocker()
        self.pressed_keys = []
        self.pressed_keys = []
        self.last_combination = ""

        self.active_entry = None
        self.previous_button_text = None
        self.set_timer = None

    def update_entry(self):
        "Add + on multi key press"
        shortcut_combination = '+'.join(self.pressed_keys)
        if hasattr(self, "active_entry") and self.active_entry is not None:
            self.active_entry.setText(shortcut_combination)

    def get_script_name(self):
        "Get profile name from entry"
        script_name = self.script_name_entry.text().strip()
        if not script_name:
            QMessageBox.warning(None, "Input Error", "Please enter a Profile name.") # noqa
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name

    def is_widget_valid(self, widget_tuple):
        "Check whether the row is valid"
        try:
            entry_widget, button_widget = widget_tuple
            return entry_widget is not None and button_widget is not None
        except ValueError:
            return False

    def key_listening(self, entry_widget, button):
        "Get and Listen to key press"
        def toggle_other_buttons(state):
            if hasattr(self, 'key_rows'):
                for key_row in self.key_rows:
                    (_, _, orig_button, remap_button, _, _, _, _) = key_row

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
                    (orig_entry, remap_entry, orig_button, _, _, _, _,
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
                        orig_entry, remap_entry, _, _, _, _, _,
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

            toggle_other_buttons(False)

            button.clicked.disconnect()
            button.clicked.connect(lambda: self.key_listening
                                   (entry_widget, button))

            self.pressed_keys = []
            self.last_combination = ""
            self.set_timer = QTimer()
            self.set_timer.setSingleShot(True)
            self.set_timer.timeout.connect(lambda:
                                               self.finalize_combination
                                               (entry_widget))
            keyboard.hook(lambda event: self.multi_key_event
                          (event, entry_widget, button))

        else:
            self.is_listening = False
            self.active_entry = None
            self.pressed_keys = []

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
                        orig_entry, remap_entry, _, _, _, _, _,
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
        "Action when multiple key is pressed, set timer before saving the key"
        if not self.is_listening or self.active_entry != entry_widget:
            return

        if hasattr(self, 'use_scan_code') and self.use_scan_code:
            key = f"SC{event.scan_code:02X}"
        else:
            key = event.name

        key_lower = key.lower()
        if key_lower in constant.changes_key:
            key = constant.changes_key[key_lower]

        if (len(key) == 1 and key.isupper() and key.isalpha()):
            key = key.lower()

        if event.event_type == "down":
            if key not in self.pressed_keys:
                self.pressed_keys.append(key)
                self.update_widget(entry_widget)
            if (hasattr(self, "release_timer")
                    and self.set_timer.isActive()):
                self.set_timer.stop()

        elif event.event_type == "up":
            if key in self.pressed_keys:
                self.pressed_keys.remove(key)
                if not self.pressed_keys:
                    self.key_listening(entry_widget, button)
                    self.request_timer_start.emit(entry_widget)

                else:
                    if hasattr(self, "release_timer"):
                        self.request_timer_start.emit(entry_widget)

    def mouse_listening(self, button, pressed):
        "Get and listen to mouse key press"
        if not (self.is_listening and self.active_entry):
            return

        if pressed and hasattr(self, "edit_window"):
            widget = self.edit_window.childAt(
                self.edit_window.mapFromGlobal(
                    self.edit_window.cursor().pos()))
            while widget:
                if isinstance(widget, QPushButton):
                    return
                widget = widget.parent()

        button_map = {
            mouse.Button.left: "Left Button",
            mouse.Button.right: "Right Button",
            mouse.Button.middle: "Middle Button"
        }
        mouse_button = button_map.get(button, getattr(
            button, "name", str(button)))

        if pressed:
            if mouse_button not in self.pressed_keys:
                self.pressed_keys.append(mouse_button)
                self.update_widget(self.active_entry)
        else:
            if mouse_button in self.pressed_keys:
                self.pressed_keys.remove(mouse_button)
                if not self.pressed_keys:
                    self.key_listening(self.active_entry, None)
                    self.request_timer_start.emit(self.active_entry)
                elif hasattr(self, "release_timer"):
                    self.request_timer_start.emit(self.active_entry)

    def release_timer(self):
        "Start the timer"
        if hasattr(self, "release_timer"):
            self.set_timer.start(400)

    def format_key_combo(self, keys):
        "Format for multiple key press"
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
        "Insert saved key into entry"
        combo = self.format_key_combo(self.pressed_keys)
        entry_widget.setText(combo)
        self.last_combination = combo

    def finalize_combination(self, entry_widget):
        "Save the combination"
        entry_widget.setText(self.last_combination)
        self.pressed_keys = []

    def disable_input(self, entry_rows):
        "Disable input. Used on key listening"
        if not hasattr(self, "_input_blocker"):
            self._input_blocker = InputBlocker()
        for entry_tuple in entry_rows:
            entry = entry_tuple[0]
            if entry is not None:
                entry.installEventFilter(self._input_blocker)

    def enable_input(self, entry_rows):
        "Enable input. Used on key listening"
        if hasattr(self, "_input_blocker"):
            for entry_tuple in entry_rows:
                entry = entry_tuple[0]
                if entry is not None:
                    entry.removeEventFilter(self._input_blocker)

    def load_key_list(self):
        "Load list of hard coded key from json file"
        key_map = {}
        try:
            with open(constant.keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key, info in keys.items():
                            readable = key
                            raw = info.get("translate", "")
                            if raw:
                                key_map[raw] = readable
        except FileNotFoundError as e:
            print(f"Error reading key list: {e}")
        return key_map
    
    def load_key_translations(self):
        "Load translation from raw key to readable key"
        key_translations = {}
        try:
            with open(constant.keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key, info in keys.items():
                            readable_key = key.strip().lower()
                            translation = info.get("translate", "").strip()
                            if translation:
                                key_translations[readable_key] = translation

        except FileNotFoundError as e:
            print(f"Error reading key translations: {e}")
        return key_translations

    def translate_key(self, key, key_translations):
        "Translate raw key into readable key"
        keys = key.split('+')
        translated_keys = []

        for single_key in keys:
            translated_key = key_translations.get(single_key.strip().lower(),
                                                    single_key.strip())
            translated_keys.append(translated_key)

        return " & ".join(translated_keys)
