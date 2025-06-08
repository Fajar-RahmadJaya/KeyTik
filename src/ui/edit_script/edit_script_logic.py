import os
import webbrowser
import keyboard
from pynput import mouse
from PySide6.QtWidgets import (
    QMessageBox, QDialog, QLabel, QVBoxLayout, QWidget, QTextEdit
)
from PySide6.QtCore import Qt
from src.utility.constant import (interception_install_path)

class EditScriptLogic:
    def check_ahk_installation(self, show_installed_message=False):
        """
        Check if AutoHotkey v2 is installed
        :param show_installed_message: Boolean to control whether to show success message
        :return: Boolean indicating if AHK is installed
        """
        ahk_path = r"C:\Program Files\AutoHotkey\v2"

        if os.path.exists(ahk_path):
            if show_installed_message:
                QMessageBox.information(None, "AHK Installation", "AutoHotkey v2 is installed on your system.")
            return True
        else:
            reply = QMessageBox.question(
                None,
                "AHK Installation",
                "AutoHotkey v2 is not installed on your system. AutoHotkey is required for KeyTik to work.\n\nWould you like to download it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("https://www.autohotkey.com/")
            return False

    def check_interception_driver(self):
        """
        Check if Interception driver is installed
        :return: Boolean indicating if driver is installed
        """
        driver_path = r"C:\Windows\System32\drivers\keyboard.sys"

        if os.path.exists(driver_path):
            return True
        else:
            reply = QMessageBox.question(
                None,
                "Driver Not Found",
                "Interception driver is not installed. This driver is required to use assign on specific device feature.\n \n \nNote: Restart your device after installation.\n"
                "Would you like to install it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if os.path.exists(interception_install_path):
                        # Get the directory containing the batch file
                        install_dir = os.path.dirname(interception_install_path)

                        # Use ctypes to elevate privileges and run the batch file from its directory
                        import ctypes
                        ctypes.windll.shell32.ShellExecuteW(
                            None,
                            "runas",  # Run as administrator
                            "cmd.exe",
                            f"/k cd /d {install_dir} && {os.path.basename(interception_install_path)}",  # Change to correct directory first
                            None,
                            1  # SW_SHOWNORMAL
                        )
                    else:
                        QMessageBox.critical(
                            None,
                            "Installation Failed",
                            "Installation script not found. Please check your installation."
                        )
                except Exception as e:
                    QMessageBox.critical(None, "Error", f"An error occurred during installation: {str(e)}")
            return False

    def show_tooltip(self, event, tooltip_text):
        # PySide6 tooltip using QLabel in a QDialog
        tooltip = QDialog()
        tooltip.setWindowFlags(Qt.WindowType.ToolTip)
        tooltip.move(event.globalX() + 10, event.globalY() + 10)
        label = QLabel(tooltip_text, tooltip)
        label.setStyleSheet("background-color: white; color: black; border: 1px solid gray; padding: 5px;")
        layout = QVBoxLayout(tooltip)
        layout.addWidget(label)
        tooltip.setLayout(layout)
        tooltip.show()
        self.tooltip = tooltip

    def update_entry(self):
        shortcut_combination = '+'.join(self.pressed_keys)  # Join the keys and buttons into a string
        if hasattr(self, "active_entry") and self.active_entry is not None:
            if hasattr(self.active_entry, "setCurrentText"):
                self.active_entry.setCurrentText(shortcut_combination)
            elif hasattr(self.active_entry, "setText"):
                self.active_entry.setText(shortcut_combination)

    def process_shortcuts(self, file, key_translations):
        for shortcut_row in self.shortcut_rows:
            if self.is_widget_valid(shortcut_row):
                try:
                    shortcut_entry, _ = shortcut_row
                    shortcut_key = shortcut_entry.currentText().strip()
                    if shortcut_key:
                        translated_key = self.translate_key(shortcut_key, key_translations)
                        if "&" in translated_key:
                            file.write(f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                        else:
                            file.write(f"~{translated_key}::\n{{\n    global toggle\n    toggle := !toggle\n}}\n\n")
                except Exception:
                    continue

    def process_key_remaps(self, file, key_translations):
        for row in self.key_rows:
            if len(row) >= 7:
                original_key_entry, remap_key_entry, original_key_select, remap_key_select, text_format_var, hold_format_var, hold_interval_entry = row
                try:
                    original_key = original_key_entry.currentText().strip()
                    remap_key = remap_key_entry.currentText().strip()

                    if original_key and remap_key:
                        has_multiple_keys = "+" in original_key
                        original_translated = self.translate_key(original_key, key_translations)

                        if has_multiple_keys:
                            keys = [k.strip() for k in original_key.split("+")]
                            if len(keys) == 2 and keys[0] == keys[1]:
                                single_key = self.translate_key(keys[0], key_translations)
                                if text_format_var.isChecked():
                                    file.write(f'*{single_key}::{{\n')
                                    file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                    file.write(f'        SendText("{remap_key}")\n')
                                    file.write('    }\n')
                                    file.write('}\n')
                                elif hold_format_var.isChecked():
                                    # --- CHANGED: Default hold_interval to "10" if entry is None or empty ---
                                    if hold_interval_entry is None or not hold_interval_entry.text().strip() or hold_interval_entry.text().strip() == "Hold Interval":
                                        hold_interval = "10"
                                    else:
                                        hold_interval = hold_interval_entry.text().strip()
                                    hold_interval_ms = str(int(float(hold_interval) * 1000))
                                    if "+" in remap_key:
                                        remap_keys = [self.translate_key(key.strip(), key_translations) for key in remap_key.split("+")]
                                        down_sequence = "".join([f"{{{key} Down}}" for key in remap_keys])
                                        up_sequence = "".join([f"{{{key} Up}}" for key in reversed(remap_keys)])
                                        file.write(f'*{single_key}::{{\n')
                                        file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                        file.write(f'        Send("{down_sequence}"), SetTimer(Send.Bind("{up_sequence}"), -{hold_interval_ms})\n')
                                        file.write('    }\n')
                                        file.write('}\n')
                                    else:
                                        remap_key_tr = self.translate_key(remap_key, key_translations)
                                        file.write(f'*{single_key}::{{\n')
                                        file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                        file.write(f'        Send("{{{remap_key_tr} Down}}")\n')
                                        file.write(f'        SetTimer(() => Send("{{{remap_key_tr} Up}}"), -{hold_interval_ms})\n')
                                        file.write('    }\n')
                                        file.write('}\n')
                                else:
                                    if "+" in remap_key:
                                        keys = [self.translate_key(key.strip(), key_translations) for key in remap_key.split("+")]
                                        key_down = "".join([f"{{{key} down}}" for key in keys])
                                        key_up = "".join([f"{{{key} up}}" for key in reversed(keys)])
                                        file.write(f'*{single_key}::{{\n')
                                        file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                        file.write(f'        Send("{key_down}{key_up}")\n')
                                        file.write('    }\n')
                                        file.write('}\n')
                                    else:
                                        remap_key_tr = self.translate_key(remap_key, key_translations)
                                        file.write(f'*{single_key}::{{\n')
                                        file.write(f'    if (A_PriorHotkey = "*{single_key}") and (A_TimeSincePriorHotkey < 400) {{\n')
                                        file.write(f'        Send("{remap_key_tr}")\n')
                                        file.write('    }\n')
                                        file.write('}\n')
                                continue

                        if has_multiple_keys:
                            original_translated = "~" + original_translated

                        if text_format_var.isChecked():
                            file.write(f'{original_translated}::SendText("{remap_key}")\n')
                        elif hold_format_var.isChecked():
                            # --- CHANGED: Default hold_interval to "10" if entry is None or empty ---
                            if hold_interval_entry is None or not hold_interval_entry.text().strip() or hold_interval_entry.text().strip() == "Hold Interval":
                                hold_interval = "10"
                            else:
                                hold_interval = hold_interval_entry.text().strip()
                            hold_interval_ms = str(int(float(hold_interval) * 1000))

                            if "+" in remap_key:
                                remap_keys = [self.translate_key(key.strip(), key_translations) for key in remap_key.split("+")]
                                down_sequence = "".join([f"{{{key} Down}}" for key in remap_keys])
                                up_sequence = "".join([f"{{{key} Up}}" for key in reversed(remap_keys)])

                                if has_multiple_keys:
                                    file.write(f'{original_translated}:: Send("{down_sequence}"), SetTimer(Send.Bind("{up_sequence}"), -{hold_interval_ms})\n')
                                else:
                                    file.write(f'*{original_translated}:: Send("{down_sequence}"), SetTimer(Send.Bind("{up_sequence}"), -{hold_interval_ms})\n')
                            else:
                                remap_key_tr = self.translate_key(remap_key, key_translations)
                                if has_multiple_keys:
                                    file.write(f'{original_translated}:: Send("{{{remap_key_tr} Down}}"), SetTimer(Send.Bind("{{{remap_key_tr} Up}}"), -{hold_interval_ms})\n')
                                else:
                                    file.write(f'*{original_translated}:: Send("{{{remap_key_tr} Down}}"), SetTimer(Send.Bind("{{{remap_key_tr} Up}}"), -{hold_interval_ms})\n')
                        elif "+" in remap_key:
                            keys = [key.strip() for key in remap_key.split("+")]
                            key_down = "".join([f"{{{key} down}}" for key in keys])
                            key_up = "".join([f"{{{key} up}}" for key in reversed(keys)])
                            file.write(f'{original_translated}::Send("{key_down}{key_up}")\n')
                        else:
                            remap_key_tr = self.translate_key(remap_key, key_translations)
                            file.write(f'{original_translated}::{remap_key_tr}\n')
                except Exception:
                    continue

    def get_script_name(self):
        script_name = self.script_name_entry.text().strip()
        if not script_name:
            QMessageBox.warning(None, "Input Error", "Please enter a Profile name.")
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name

    def is_widget_valid(self, widget_tuple):
        """Check if a widget tuple exists and is valid"""
        try:
            entry_widget, button_widget = widget_tuple
            return entry_widget is not None and button_widget is not None
        except Exception:
            return False

    def toggle_shortcut_key_listening(self, entry_widget, button):
        def toggle_other_buttons(state):
            # Disable/Enable all buttons except the active one
            if hasattr(self, 'key_rows'):
                for key_row in self.key_rows:
                    orig_entry, remap_entry, orig_button, remap_button, text_format_var, hold_format_var, hold_interval_entry = key_row
                    if orig_button != button and orig_button is not None:
                        orig_button.setEnabled(state)
                    if remap_button != button and remap_button is not None:
                        remap_button.setEnabled(state)
            for shortcut_entry, shortcut_button in self.shortcut_rows:
                if shortcut_button != button and shortcut_button is not None:
                    shortcut_button.setEnabled(state)

        if not self.is_listening:
            # Start listening
            self.is_listening = True
            self.active_entry = entry_widget
            self.previous_button_text = button.text()

            # Disable user input for all relevant entries
            entries_to_disable = []
            if hasattr(self, 'script_name_entry'):
                entries_to_disable.append((self.script_name_entry, None))
            if hasattr(self, 'keyboard_entry'):
                entries_to_disable.append((self.keyboard_entry, None))
            if hasattr(self, 'program_entry'):
                entries_to_disable.append((self.program_entry, None))
            if hasattr(self, 'original_key_entry'):
                entries_to_disable.append((self.original_key_entry, None))
            if hasattr(self, 'remap_key_entry'):
                entries_to_disable.append((self.remap_key_entry, None))
            if hasattr(self, 'shortcut_entry'):
                entries_to_disable.append((self.shortcut_entry, None))
            if hasattr(self, 'hold_interval_entry'):
                entries_to_disable.append((self.hold_interval_entry, None))
            self.disable_entry_input(entries_to_disable)

            self.ignore_next_click = True  # Ignore the first left-click

            # Disable other buttons
            toggle_other_buttons(False)

            # Change button text
            button.setText("Save Selected Key")
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.toggle_shortcut_key_listening(entry_widget, button))

            # Start keyboard listener if not already hooked
            if not self.hook_registered:
                keyboard.hook(self.on_shortcut_key_event)
                self.hook_registered = True

            # Start mouse listener if not already running
            if self.mouse_listener is None:
                self.mouse_listener = mouse.Listener(on_click=self.on_shortcut_mouse_event)
                self.mouse_listener.start()

        else:
            # Stop listening
            self.is_listening = False
            self.active_entry = None

            entries_to_enable = []
            if hasattr(self, 'script_name_entry'):
                entries_to_enable.append((self.script_name_entry, None))
            if hasattr(self, 'keyboard_entry'):
                entries_to_enable.append((self.keyboard_entry, None))
            if hasattr(self, 'program_entry'):
                entries_to_enable.append((self.program_entry, None))
            if hasattr(self, 'original_key_entry'):
                entries_to_enable.append((self.original_key_entry, None))
            if hasattr(self, 'remap_key_entry'):
                entries_to_enable.append((self.remap_key_entry, None))
            if hasattr(self, 'shortcut_entry'):
                entries_to_enable.append((self.shortcut_entry, None))
            if hasattr(self, 'hold_interval_entry'):
                entries_to_enable.append((self.hold_interval_entry, None))
            self.enable_entry_input(entries_to_enable)

            # Enable all buttons
            toggle_other_buttons(True)

            # Reset button text
            button.setText(self.previous_button_text)
            button.clicked.disconnect()
            button.clicked.connect(lambda: self.toggle_shortcut_key_listening(entry_widget, button))

            # Unhook keyboard listener
            if self.hook_registered:
                keyboard.unhook_all()
                self.hook_registered = False

            # Stop mouse listener
            if self.mouse_listener is not None:
                self.mouse_listener.stop()
                self.mouse_listener = None

    def on_key_event(self, event):
        if self.is_listening and self.active_entry and event.event_type == 'down':
            key_pressed = event.name
            if hasattr(self.active_entry, "setCurrentText"):
                self.active_entry.setCurrentText(key_pressed)
            elif hasattr(self.active_entry, "setText"):
                self.active_entry.setText(key_pressed)

    def on_mouse_event(self, x, y, button, pressed):
        if self.is_listening and self.active_entry:
            if self.ignore_next_click and button == mouse.Button.left and pressed:
                self.ignore_next_click = False
                return
            if pressed:
                if button == mouse.Button.left:
                    mouse_button = "Left Click"
                elif button == mouse.Button.right:
                    mouse_button = "Right Click"
                elif button == mouse.Button.middle:
                    mouse_button = "Middle Click"
                else:
                    mouse_button = str(button)
                if hasattr(self.active_entry, "setCurrentText"):
                    self.active_entry.setCurrentText(mouse_button)
                elif hasattr(self.active_entry, "setText"):
                    self.active_entry.setText(mouse_button)

    def handle_shortcut_key_event(self, event):
        if self.is_listening and self.active_entry is not None:
            self.active_entry.setEnabled(True)
            # Insert the key press into the entry widget
            if hasattr(self.active_entry, "text") and hasattr(self.active_entry, "setCurrentText"):
                current_text = self.active_entry.currentText()
                self.active_entry.setCurrentText(current_text + event.name)
            elif hasattr(self.active_entry, "text") and hasattr(self.active_entry, "setText"):
                current_text = self.active_entry.text()
                self.active_entry.setText(current_text + event.name)
            self.active_entry.setEnabled(False)

    def disable_entry_input(self, key_rows):
        # Process each entry in the key_rows list
        for entry_tuple in key_rows:
            entry = entry_tuple[0]  # Get the entry widget from the tuple
            if entry is not None:
                entry.setEnabled(False)

    def enable_entry_input(self, key_rows):
        for entry_tuple in key_rows:
            entry = entry_tuple[0]
            if entry is not None:
                entry.setEnabled(True)

    def replace_raw_keys(self, key, key_map):
        return key_map.get(key, key)  # If key not found in the map, return the key as is.