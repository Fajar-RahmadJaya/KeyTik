"Write AutoHotkey script"

from dataclasses import dataclass
import os
import json
import random
import traceback
import re
from PySide6.QtWidgets import (QMessageBox, QLineEdit, QCheckBox)  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from utility import constant

from utility import utils


@dataclass
class KeyRows:
    "Dataclass containing key rows tuple"
    default_key_entry: QLineEdit = None
    remap_key_entry: QLineEdit = None
    text_format_checkbox: QCheckBox = None
    hold_format_checkbox: QCheckBox = None
    hold_interval_entry: QLineEdit = None
    first_key_checkbox: QCheckBox = None


class WriteScript():
    "Write script based on profile input"
    def __init__(self):
        super().__init__()
        self.is_text_mode = None
        self.scripts = None
        self.key_rows = None

    def save_changes(self, script_name, mode_combobox):
        "Write script"
        script_name = self.get_script_name()  # pylint: disable=E1101
        if not script_name:
            return

        if not self.check_key_integrity():
            return

        try:
            mode = mode_combobox.currentText().strip().lower()
            self.is_text_mode = mode == "text mode"
            self.handle_write(script_name, mode)
            self.scripts = self.list_scripts() # pylint: disable=E1101
            self.update_script_list() # pylint: disable=E1101
            self.edit_window.destroy() # pylint: disable=E1101

        except ValueError as e:
            print(f"Error writing script: {e}")
            traceback.print_exc()

    def handle_write(self, script_name, mode):
        "Action when saving profile (Can be moved)"
        output_path = os.path.join(self.script_dir, script_name) # pylint: disable=E1101
        key_translations = self.load_key_translations() # pylint: disable=E1101

        with open(output_path, 'w', encoding='utf-8') as file:
            if mode == "text mode":
                self.handle_text_mode(file)
            elif mode == "default mode":
                self.handle_default_mode(file)
            else:
                self.pro_write(file, mode, key_translations) # pylint: disable=E1101

    def handle_default_mode(self, file):
        "Write default mode"
        file.write("; default\n")
        self.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")
        file.write("#Requires AutoHotkey v2.0\n")

        write_hotif = self.write_condition(file,
                                            write_shortcuts=True,
                                            write_program=True,
                                            write_device=True)

        self.process_key_remaps(file)

        if write_hotif:
            file.write("#HotIf\n")

    def process_key_remaps(self, file):
        "Handle key remap write"
        for row in self.key_rows:
            (default_key_entry, remap_key_entry, _,
            _, text_format_checkbox, hold_format_checkbox,
            hold_interval_entry, first_key_checkbox, _) = row

            self.key_rows = KeyRows(
                default_key_entry =default_key_entry,
                remap_key_entry = remap_key_entry,
                text_format_checkbox = text_format_checkbox,
                hold_format_checkbox = hold_format_checkbox,
                hold_interval_entry = hold_interval_entry,
                first_key_checkbox = first_key_checkbox
            )

            try:
                default_key = default_key_entry.text().strip()
                remap_key = remap_key_entry.text().strip()

                if not default_key or not remap_key:
                    continue

                has_multiple_keys = "+" in default_key

                if has_multiple_keys:
                    keys = [k.strip() for k in default_key.split("+")]
                    if len(keys) == 2 and keys[0] == keys[1]:
                        self.write_double_click(
                            file, keys[0], remap_key
                        )
                        continue
                    default_translated = self.write_multiple_key_default(default_key)

                else:
                    default_translated = self.write_single_key_default(
                        default_key)

                self.handle_remap_type(file, default_translated, remap_key)

            except ValueError:
                continue

    def handle_text_mode(self, file):
        "Write text mode"
        file.write("; text\n")
        self.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")
        file.write("#Requires AutoHotkey v2.0\n")

        write_hotif = self.write_condition(file,
                                            write_shortcuts=True,
                                            write_program=True,
                                            write_device=True)

        text_content = self.text_block.toPlainText().strip() # pylint: disable=E1101
        if text_content:
            file.write("; Text mode start\n")
            file.write(text_content + '\n')
            file.write("; Text mode end\n")

        if write_hotif:
            file.write("#HotIf\n")

    def generate_exit_key(self, script_name, file=None):
        "Generate key for profile exit"
        possible_keys = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'] 

        try:
            if os.path.exists(constant.exit_keys_file):
                try:
                    with open(constant.exit_keys_file, 'r', encoding='utf-8') as f:
                        exit_keys = json.load(f)
                except json.JSONDecodeError:
                    exit_keys = {}
            else:
                exit_keys = {}

            used_keys = set(key[-1] for key in exit_keys.values())
            available_keys = [k for k in possible_keys if k not in used_keys]

            if not available_keys:
                available_keys = possible_keys

            exit_combo = f"^!{random.choice(available_keys)}"

            exit_keys[script_name] = exit_combo
            with open(constant.exit_keys_file, 'w', encoding='utf-8') as f:
                json.dump(exit_keys, f)

            if file is not None:
                file.write(f"{exit_combo}::ExitApp\n\n")

            return exit_combo

        except FileNotFoundError as e:
            print(f"Error handling exit key: {e}")
            if file is not None:
                file.write("^!p::ExitApp\n\n")
            return "^!p"

    def initialize_exit_keys(self):
        "Make sure there is no duplicate exit key usage on each script"
        try:
            # Resolve and get exit keys from file
            exit_keys =  self.resolve_exit_files_conflict()

            # Make sure each script have different exit keys
            self.validate_exit_keys(exit_keys)

            # Save the new exit keys back to save file
            try:
                with open(constant.exit_keys_file, 'w', encoding='utf-8') as f:
                    json.dump(exit_keys, f)
            except FileNotFoundError as e:
                print(f"Error saving exit_keys.json: {e}")

        except FileNotFoundError as e:
            print(f"Error in initialize_exit_keys: {e}")

    def validate_exit_keys(self, exit_keys):
        "Make sure each script have different exit keys"
        # Collect all ahk script from active and store dit
        ahk_files = set()
        for ahk_path in [utils.active_dir, utils.store_dir]:
            if os.path.exists(ahk_path):
                ahk_files.update(f for f in os.listdir(ahk_path) if f.endswith('.ahk'))

        # Remove exit key from save file for script that no longer exist
        for key in [key for key in exit_keys if key not in ahk_files]:
            del exit_keys[key]

        # Ensure all scripts have a unique exit key
        for script_name in ahk_files:
            if (script_name not in exit_keys or exit_keys[script_name][-1] in [exit_keys[s][-1]
                    for s in exit_keys if s != script_name]):
                # If script has no exit key or its key is already used, assign a new one
                possible_keys = list('abcdefghijklmnopqrstuvwxyz')
                used_keys = set(exit_keys[s][-1]
                                for s in exit_keys
                                if s != script_name)
                available_keys = [k for k in possible_keys
                                    if k not in used_keys]
                if not available_keys:
                    available_keys = possible_keys
                exit_keys[script_name] = f"^!{random.choice(available_keys)}"
            exit_combo = exit_keys[script_name]

            # Make sure ahk script using the correct exit keys
            for dir_path in [utils.active_dir, utils.store_dir]:
                script_path = os.path.join(dir_path, script_name)
                if os.path.exists(script_path):
                    try:
                        with open(script_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        if len(lines) < 2:
                            lines += ['\n'] * (2 - len(lines))
                        lines[1] = f"{exit_combo}::ExitApp\n"
                        with open(script_path, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                    except FileNotFoundError as e:
                        print(f"Error processing {script_name} in {dir_path}: {e}")
                        continue

    def resolve_exit_files_conflict(self):
        "Resolve and get exit keys from file"
        # Load the exit keys from save file
        exit_keys = {}
        if os.path.exists(constant.exit_keys_file):
            try:
                with open(constant.exit_keys_file, 'r', encoding='utf-8') as f:
                    exit_keys = json.load(f)
            except FileNotFoundError:
                exit_keys = {}

        # Create dictionary containing script and the exit key
        combo_to_scripts = {}
        for script, combo in exit_keys.items():
            combo_to_scripts.setdefault(combo, []).append(script)

        possible_keys = list('abcdefghijklmnopqrstuvwxyz')
        used_keys = set()

        # Resolve exit keys conflict if there any
        for combo, scripts in combo_to_scripts.items():
            if len(scripts) == 1:
                # Only one script uses this combo, mark the key as used
                used_keys.add(combo[-1:])
            else:
                # Multiple scripts use the same combo, only the first keeps it
                used_keys.add(combo[-1:])
                for script in scripts[1:]:
                    # Assign a new, unused key to the rest
                    available_keys = [k for k in possible_keys
                                        if k not in used_keys]
                    if not available_keys:
                        available_keys = possible_keys
                    new_key = random.choice(available_keys)
                    used_keys.add(new_key)
                    exit_keys[script] = f"^!{new_key}"

        return exit_keys

    def check_key_integrity(self):
        "Make sure there is no conflict on profile input"
        shortcut_types = {"normal": [], "caps": []}
        caps_on_present = False
        caps_off_present = False
        num_on_present = False
        num_off_present = False
        for shortcut_row in self.shortcut_rows: # pylint: disable=E1101
            if self.is_widget_valid(shortcut_row): # pylint: disable=E1101
                shortcut = shortcut_row[0].text().strip()
                if shortcut:
                    if shortcut.lower() == "capslock on":
                        shortcut_types["caps"].append(shortcut)
                        caps_on_present = True
                    elif shortcut.lower() == "capslock off":
                        shortcut_types["caps"].append(shortcut)
                        caps_off_present = True
                    elif shortcut.lower() == "numlock on":
                        shortcut_types["caps"].append(shortcut)
                        num_on_present = True
                    elif shortcut.lower() == "numlock off":
                        shortcut_types["caps"].append(shortcut)
                        num_off_present = True
                    else:
                        shortcut_types["normal"].append(shortcut)

        if shortcut_types["normal"] and shortcut_types["caps"]:
            msg = (QMessageBox(self.edit_window
                               if hasattr(self, "edit_window")
                               else None))
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use 'CapsLock On' or 'CapsLock Off' "
                        "or 'NumLock On' or 'Numlock Off' together with normal keys as shortcuts. "
                        "Please use only one type "
                        "(either normal keys or CapsLock NumLock ON/OFF) for all shortcuts.")
            msg.setWindowIcon(QIcon(constant.icon_path))
            msg.exec()
            return False
        if caps_on_present and caps_off_present:
            msg = (QMessageBox(self.edit_window
                               if hasattr(self, "edit_window")
                               else None))
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use both 'CapsLock ON' and 'CapsLock OFF' at the same time. "
                        "Please use only one of of them. If you need both, just use 'Caps Lock'.")
            msg.setWindowIcon(QIcon(constant.icon_path))
            msg.exec()
            return False
        if num_on_present and num_off_present:
            msg = (QMessageBox(self.edit_window
                               if hasattr(self, "edit_window")
                               else None))
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use both 'NumLock ON' and 'NumLock OFF' at the same time. "
                        "Please use only one of of them. If you need both, just use 'Caps Lock'.")
            msg.setWindowIcon(QIcon(constant.icon_path))
            msg.exec()
            return False
        return True

    def get_program_condition(self):
        "Get program binding value from entry"
        program_entry = self.program_entry.text().strip() # pylint: disable=E1101
        program_condition = ""

        if program_entry:
            pattern = r"\[(Tittle|Class|Process),\s*([^\]]+)\]"
            matches = re.findall(pattern, program_entry)
            conditions = []
            for typ, value in matches:
                value = value.strip()
                if typ.lower() == "process":
                    conditions.append(f'WinActive("ahk_exe {value}")')
                elif typ.lower() == "class":
                    conditions.append(f'WinActive("ahk_class {value}")')
                elif typ.lower() == "tittle":
                    conditions.append(f'WinActive("{value}")')
            program_condition = " || ".join(conditions)

        return program_condition

    def get_device_condition(self):
        "Get device binding value from entry"
        device_condition = ""
        device_name = self.keyboard_entry.text().strip() # pylint: disable=E1101
        if device_name:
            device_condition = "cm1.IsActive"
        return device_condition

    def write_condition(self, file, write_shortcuts=False,
                        write_program=False, write_device=False):
        "Write Hotif condition for shortcuts, device, program in one hotif line"
        program = self.get_program_condition() if write_program else None

        hotif_conditions = []

        # Shortcuts condition
        self.shortcuts_condition(file, hotif_conditions, write_shortcuts)

        # Device condition
        self.device_condition(file, hotif_conditions, write_device)

        if program:
            hotif_conditions.append(f"({program})")

        if hotif_conditions:
            file.write("SetTitleMatchMode 2\n")
            file.write(f"#HotIf {' && '.join(hotif_conditions)}\n")
            return True
        return False

    def device_condition(self, file, hotif_conditions, write_device):
        "Device condition"
        device = self.keyboard_entry.text().strip() if write_device else None # pylint: disable=E1101
        if device:
            parts = device.split(",", 1)
            device_type = parts[0].strip().lower()
            vid_pid_or_handle = parts[1].strip() if len(parts) > 1 else ""
            if device_type == "mouse":
                is_mouse = True
            elif device_type == "keyboard":
                is_mouse = False
            else:
                raise ValueError(f"Unknown device type: {device_type}")
            file.write("Persistent\n")
            file.write("#include AutoHotkey Interception\\Lib\\AutoHotInterception.ahk\n\n")
            file.write("AHI := AutoHotInterception()\n")
            file.write(
                (
                f'id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, '
                f'"{vid_pid_or_handle}")\n'
                )
            )
            file.write("cm1 := AHI.CreateContextManager(id1)\n\n")
            hotif_conditions.append("cm1.IsActive")

    def shortcuts_condition(self, file, hotif_conditions, write_shortcuts=False):
        "Shortcuts condition"
        shortcuts = None
        if write_shortcuts:
            shortcuts = [
                shortcut_row[0].text().strip()
                for shortcut_row in self.shortcut_rows # pylint: disable=E1101
                if self.is_widget_valid(shortcut_row) # pylint: disable=E1101
                and shortcut_row[0].text().strip()
            ] or None

        if shortcuts:
            valid_shortcuts = [s for s in shortcuts if s]
            if valid_shortcuts:
                caps_shortcuts = []
                normal_shortcuts = []
                for shortcut in valid_shortcuts:
                    if shortcut.lower() == "capslock on":
                        caps_shortcuts.append('GetKeyState("CapsLock", "T")')
                    elif shortcut.lower() == "capslock off":
                        caps_shortcuts.append('!GetKeyState("CapsLock", "T")')
                    elif shortcut.lower() == "numlock on":
                        caps_shortcuts.append('GetKeyState("NumLock", "T")')
                    elif shortcut.lower() == "numlock off":
                        caps_shortcuts.append('!GetKeyState("NumLock", "T")')
                    else:
                        normal_shortcuts.append(shortcut)
                if normal_shortcuts:
                    file.write("toggle := false\n\n")
                    for shortcut in normal_shortcuts:
                        translated_shortcut = self.translate_key(shortcut) # pylint: disable=E1101
                        file.write(f"~{translated_shortcut}:: ; Shortcuts\n")
                        file.write("{\n    global toggle\n    toggle := !toggle\n}\n\n")
                    hotif_conditions.append("toggle")
                elif caps_shortcuts:
                    hotif_conditions.append(" || ".join(caps_shortcuts))

    def handle_remap_type(self, file, default_translated, remap_key):
        "Handle text, hold, single, multiple key mode"
        if self.key_rows.text_format_checkbox.isChecked():
            self.write_text_format(file, default_translated, remap_key)
        elif self.key_rows.hold_format_checkbox.isChecked():
            self.write_hold_format(file, default_translated, remap_key)
        elif "+" in remap_key:
            self.write_multiple_key_remap(file, default_translated,
                                          remap_key)
        else:
            self.write_single_key_remap(file, default_translated,
                                        remap_key)

    def write_single_key_default(self, default_key):
        "Write single key case on default key"
        translated_key = self.translate_key(default_key) # pylint: disable=E1101
        return translated_key

    def write_single_key_remap(self, file, default_translated, remap_key):
        "Write single key case on remap key"
        if self.is_unicode_key(remap_key): # pylint: disable=E1101
            file.write(f'{default_translated}::SendInput Chr({ord(remap_key)})\n')
        else:
            remap_key_tr = self.translate_key(remap_key) # pylint: disable=E1101
            file.write(f'{default_translated}::{remap_key_tr}\n')

    def write_multiple_key_default(self, default_key):
        "Write multiple key case on default key"
        if (self.key_rows.first_key_checkbox is not None
            and self.key_rows.first_key_checkbox.isChecked()):
            translated_key = self.translate_key(default_key) # pylint: disable=E1101
        else:
            translated_key = "~" + self.translate_key(default_key) # pylint: disable=E1101
        return translated_key

    def write_multiple_key_remap(self, file, default_translated, remap_key):
        "Write multiple key case on remap key"
        keys = [key.strip() for key in remap_key.split("+")]
        send_parts_down = []
        send_parts_up = []

        for key in keys:
            if hasattr(self, "is_unicode_key") and self.is_unicode_key(key): # pylint: disable=E1101
                send_parts_down.append(f'{{" Chr({ord(key)}) " down}}')
                send_parts_up.insert(0, f'{{" Chr({ord(key)}) " up}}')
            else:
                tr_key = self.translate_key(key) # pylint: disable=E1101
                send_parts_down.append(f'{{{tr_key} down}}')
                send_parts_up.insert(0, f'{{{tr_key} up}}')

        send_sequence = "".join(send_parts_down + send_parts_up)
        file.write(f'{default_translated}::SendInput("{send_sequence}")\n')

    def write_double_click(self, file, single_key, remap_key):
        "Write double click (same key twice) on default key"
        translated_key = self.translate_key(single_key) # pylint: disable=E1101

        file.write(f'*{translated_key}::{{\n')
        file.write(
            (f'    if (A_PriorHotkey = "*{translated_key}") '
             'and (A_TimeSincePriorHotkey < 400)\n'
            )
        )

        if self.key_rows.text_format_checkbox.isChecked():
            file.write(f'        SendText("{remap_key}")\n')
        elif self.key_rows.hold_format_checkbox.isChecked():
            self.hold_format_double_click(remap_key, file)
        else:
            if "+" in remap_key:
                keys = [key.strip() for key in remap_key.split("+")]
                send_parts_down = []
                send_parts_up = []

                for key in keys:
                    if (hasattr(self, "is_unicode_key") and
                            self.is_unicode_key(key)): # pylint: disable=E1101
                        send_parts_down.append(f'{{" Chr({ord(key)}) " down}}')
                        send_parts_up.insert(0, f'{{" Chr({ord(key)}) " up}}')
                    else:
                        tr_key = self.translate_key(key) # pylint: disable=E1101
                        send_parts_down.append(f'{{{tr_key} down}}')
                        send_parts_up.insert(0, f'{{{tr_key} up}}')

                send_sequence = "".join(send_parts_down + send_parts_up)
                file.write(f'        SendInput("{send_sequence}")\n')
            else:
                if (hasattr(self, "is_unicode_key") and
                        self.is_unicode_key(remap_key)): # pylint: disable=E1101
                    file.write(f'        Send Chr({ord(remap_key)})\n')
                else:
                    remap_key_tr = self.translate_key(remap_key) # pylint: disable=E1101
                    file.write(f'        SendInput("{remap_key_tr}")\n')

        file.write('    }\n')

    def hold_format_double_click(self, remap_key, file):
        "Write double click on hold format"
        hold_interval_ms = "10000"
        if (self.key_rows.hold_format_checkbox.isChecked()
            and self.key_rows.hold_interval_entry is not None):
            hold_interval = "10"
            if (self.key_rows.hold_interval_entry.text().strip() and
                self.key_rows.hold_interval_entry.text().strip()
                    != "Hold Interval"):
                hold_interval =self.key_rows. hold_interval_entry.text().strip()
            hold_interval_ms = str(int(float(hold_interval) * 1000))

        keys = [key.strip() for key in remap_key.split("+")]
        down_parts = []
        up_parts = []

        for key in keys:
            if (hasattr(self, "is_unicode_key") and
                    self.is_unicode_key(key)): # pylint: disable=E1101
                down_parts.append(f'{{" Chr({ord(key)}) " Down}}')
                up_parts.insert(0, f'{{" Chr({ord(key)}) " Up}}')
            else:
                tr_key = self.translate_key(key) # pylint: disable=E1101
                down_parts.append(f'{{{tr_key} Down}}')
                up_parts.insert(0, f'{{{tr_key} Up}}')

        down_sequence = "".join(down_parts)
        up_sequence = "".join(up_parts)

        file.write(
            (f'        (SendInput("{down_sequence}"), '
                f'SetTimer(() => SendInput("{up_sequence}"), -{hold_interval_ms}))\n'
            )
        )

    def write_text_format(self, file, default_translated, remap_key):
        "write text format (Send literal string)"
        file.write(f'{default_translated}::SendText("{remap_key}")\n')

    def write_hold_format(self, file, default_translated, remap_key):
        "Write hold format"
        hold_interval_ms = "10000"
        if (self.key_rows.hold_format_checkbox.isChecked()
            and self.key_rows.hold_interval_entry is not None):
            hold_interval = "10"
            if (self.key_rows.hold_interval_entry.text().strip() and
                self.key_rows.hold_interval_entry.text().strip()
                    != "Hold Interval"):
                hold_interval = self.key_rows.hold_interval_entry.text().strip()
            hold_interval_ms = str(int(float(hold_interval) * 1000))

        keys = [key.strip() for key in remap_key.split("+")]
        down_parts = []
        up_parts = []

        for key in keys:
            if hasattr(self, "is_unicode_key") and self.is_unicode_key(key): # pylint: disable=E1101
                down_parts.append(f'{{" Chr({ord(key)}) " Down}}')
                up_parts.insert(0, f'{{" Chr({ord(key)}) " Up}}')
            else:
                tr_key = self.translate_key(key) # pylint: disable=E1101
                down_parts.append(f'{{{tr_key} Down}}')
                up_parts.insert(0, f'{{{tr_key} Up}}')

        down_sequence = "".join(down_parts)
        up_sequence = "".join(up_parts)

        if "&" in default_translated:
            file.write(
                (
                f'{default_translated}::(SendInput("{down_sequence}"), '
                f'SetTimer(() => SendInput("{up_sequence}"), -{hold_interval_ms}))\n'
                )
            )
        else:
            file.write(
                (f'*{default_translated}::(SendInput("{down_sequence}"), '
                 f'SetTimer(() => SendInput("{up_sequence}"), -{hold_interval_ms}))\n'
                )
            )
