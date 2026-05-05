"Write AutoHotkey script"

from dataclasses import dataclass
import os
import json
import random
import re
from PySide6.QtWidgets import (QLineEdit, QCheckBox, QMessageBox)  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611

from utility import constant
from utility import utils
from utility.diff import Diff
from select_key.select_key_core import SelectKeyCore
from dashboard.dashboard_core import DashboardCore
from script_profile.remap_row_core import RemapRowCore


@dataclass
class RemapWidget:
    "Dataclass containing key rows tuple"
    default_key_entry: QLineEdit = None
    remap_key_entry: QLineEdit = None
    text_format_checkbox: QCheckBox = None
    hold_format_checkbox: QCheckBox = None
    hold_interval_entry: QLineEdit = None
    first_key_checkbox: QCheckBox = None


class WriteScript():
    "Write script based on profile input"
    def __init__(self, remap_row_comp=None):
        self.remap_row_comp = remap_row_comp

        # Composition
        self.dashboard_core = DashboardCore()
        self.remap_row_core = RemapRowCore()

    def check_key_integrity(self):
        "Make sure there is no conflict on profile input"
        shortcut_types = {"normal": [], "caps": []}
        caps_on_present = False
        caps_off_present = False
        num_on_present = False
        num_off_present = False
        for shortcut_row in self.remap_row_comp.shortcut_row_comp.shortcut_rows:
            if self.is_widget_valid(shortcut_row):
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
            msg = QMessageBox(None)
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
            msg = QMessageBox(None)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use both 'CapsLock ON' and 'CapsLock OFF' at the same time. "
                        "Please use only one of of them. If you need both, just use 'Caps Lock'.")
            msg.setWindowIcon(QIcon(constant.icon_path))
            msg.exec()
            return False
        if num_on_present and num_off_present:
            msg = QMessageBox(None)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use both 'NumLock ON' and 'NumLock OFF' at the same time. "
                        "Please use only one of of them. If you need both, just use 'Caps Lock'.")
            msg.setWindowIcon(QIcon(constant.icon_path))
            msg.exec()
            return False
        return True

    def handle_write(self, script_name, mode, keyboard_entry, program_entry):
        "Action when saving profile (Can be moved)"
        output_path = os.path.join(self.dashboard_core.script_dir, script_name)
        key_translations = self.remap_row_core.read_keylist()
        diff = Diff()  # Composition
        write_default = WriteDefault(self)  # Composition

        with open(output_path, 'w', encoding='utf-8') as file:
            if mode == "text mode":
                self.handle_text_mode(file, keyboard_entry, program_entry)
            elif mode == "default mode":
                write_default.handle_default_mode(file, keyboard_entry, program_entry)
            else:
                diff.pro_write(file, mode, key_translations)

    def handle_text_mode(self, file, keyboard_entry, program_entry):
        "Write text mode"
        file.write("; text\n")
        self.dashboard_core.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")
        file.write("#Requires AutoHotkey v2.0\n")

        write_hotif = self.write_condition(
            file, keyboard_entry, program_entry, write_shortcuts=True)

        text_content = self.remap_row_comp.text_block.toPlainText().strip()
        if text_content:
            file.write("; Text mode start\n")
            file.write(text_content + '\n')
            file.write("; Text mode end\n")

        if write_hotif:
            file.write("#HotIf\n")

    def write_condition(self, file, keyboard_entry, program_entry, write_shortcuts=False):
        "Write Hotif condition for shortcuts, device, program in one hotif line"
        hotif_conditions = []

        # Shortcuts condition
        self.shortcuts_condition(file, hotif_conditions, write_shortcuts)

        # Device condition
        self.device_condition(file, hotif_conditions, keyboard_entry)

        # Program condition
        self.get_program_condition(hotif_conditions, program_entry)

        if hotif_conditions:
            file.write("SetTitleMatchMode 2\n")
            file.write(f"#HotIf {' && '.join(hotif_conditions)}\n")
            return True
        return False

    def shortcuts_condition(self, file, hotif_conditions, write_shortcuts=False):
        "Shortcuts condition"
        shortcuts = None
        if write_shortcuts:
            shortcuts = [
                shortcut_row[0].text().strip()
                for shortcut_row in self.remap_row_comp.shortcut_row_comp.shortcut_rows
                if self.is_widget_valid(shortcut_row)
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
                        translated_shortcut = self.translate_key(shortcut)
                        file.write(f"~{translated_shortcut}:: ; Shortcuts\n")
                        file.write("{\n    global toggle\n    toggle := !toggle\n}\n\n")
                    hotif_conditions.append("toggle")
                elif caps_shortcuts:
                    hotif_conditions.append(" || ".join(caps_shortcuts))

    def get_program_condition(self, hotif_conditions, program_entry):
        "Get program binding value from entry"
        program_entry = program_entry.text().strip()

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
            hotif_conditions.append(" || ".join(conditions))

    def device_condition(self, file, hotif_conditions, keyboard_entry):
        "Device condition"
        device = keyboard_entry.text().strip()
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

    def initialize_exit_keys(self):
        "Make sure there is no duplicate exit key usage on each script"
        try:
            # Resolve and get exit keys from file
            exit_keys =  self.resolve_exit_files_conflict()

            # Make sure each script have different exit keys
            self.validate_exit_keys(exit_keys)

            # Save the new exit keys back to save file
            try:
                with open(constant.exit_keys_path, 'w', encoding='utf-8') as f:
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
        exit_keys = utils.load_exit_keys()

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

    def is_widget_valid(self, widget_tuple):
        "Check whether the row is valid"
        try:
            entry_widget, button_widget = widget_tuple
            return entry_widget is not None and button_widget is not None
        except ValueError:
            return False

    def translate_key(self, key):
        "Translate raw key into readable key"
        keys = key.split('+')
        translated_keys = []

        key_translations = self.remap_row_core.read_keylist()

        for single_key in keys:
            translated_key = key_translations.get(single_key.strip().lower())
            translated_keys.append(translated_key)

        return " & ".join(translated_keys)

    def is_unicode_key(self, key):
        "Determine whether it's unicode or hard coded key"
        select_key_core = SelectKeyCore()  # Composition
        key_data = select_key_core.load_keylist()
        for child_item in key_data.values():
            if key in child_item:
                return False
        return True

class WriteDefault():
    "Default mode writing"
    def __init__(self, write_script):
        # Parameter
        self.write_script = write_script

        # Composition
        self.remap_widget = RemapWidget()

    def handle_default_mode(self, file, keyboard_entry, program_entry):
        "Write default mode"
        dashboard_core = DashboardCore()  # Composition

        file.write("; default\n")
        dashboard_core.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")
        file.write("#Requires AutoHotkey v2.0\n")

        write_hotif = self.write_script.write_condition(
            file, keyboard_entry, program_entry, write_shortcuts=True)

        self.process_key_remaps(file)

        if write_hotif:
            file.write("#HotIf\n")

    def process_key_remaps(self, file):
        "Handle key remap write"
        for key_widget in self.write_script.remap_row_comp.key_rows:
            self.remap_widget = RemapWidget(
                default_key_entry = key_widget.default_key.default_key_entry,
                remap_key_entry = key_widget.remap_key.remap_key_entry,
                text_format_checkbox = key_widget.option.text_format_checkbox,
                hold_format_checkbox = key_widget.option.hold_format_checkbox,
                hold_interval_entry = key_widget.option.hold_interval_entry,
                first_key_checkbox = key_widget.option.first_key_checkbox
            )

            try:
                default_key = key_widget.default_key.default_key_entry.text().strip()
                remap_key = key_widget.remap_key.remap_key_entry.text().strip()

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

    def handle_remap_type(self, file, default_translated, remap_key):
        "Handle text, hold, single, multiple key mode"
        if self.remap_widget.text_format_checkbox.isChecked():
            self.write_text_format(file, default_translated, remap_key)
        elif self.remap_widget.hold_format_checkbox.isChecked():
            self.write_hold_format(file, default_translated, remap_key)
        elif "+" in remap_key:
            self.write_multiple_key_remap(file, default_translated,
                                            remap_key)
        else:
            self.write_single_key_remap(file, default_translated,
                                        remap_key)

    def write_text_format(self, file, default_translated, remap_key):
        "write text format (Send literal string)"
        file.write(f'{default_translated}::SendText("{remap_key}")\n')

    def write_hold_format(self, file, default_translated, remap_key):
        "Write hold format"
        hold_interval_ms = "10000"
        if (self.remap_widget.hold_format_checkbox.isChecked()
            and self.remap_widget.hold_interval_entry is not None):
            hold_interval = "10"
            if (self.remap_widget.hold_interval_entry.text().strip() and
                self.remap_widget.hold_interval_entry.text().strip()
                    != "Hold Interval"):
                hold_interval = self.remap_widget.hold_interval_entry.text().strip()
            hold_interval_ms = str(int(float(hold_interval) * 1000))

        keys = [key.strip() for key in remap_key.split("+")]
        down_parts = []
        up_parts = []

        for key in keys:
            if hasattr(self, "is_unicode_key") and self.write_script.is_unicode_key(key):
                down_parts.append(f'{{" Chr({ord(key)}) " Down}}')
                up_parts.insert(0, f'{{" Chr({ord(key)}) " Up}}')
            else:
                tr_key = self.write_script.translate_key(key)
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

    def write_multiple_key_remap(self, file, default_translated, remap_key):
        "Write multiple key case on remap key"
        keys = [key.strip() for key in remap_key.split("+")]
        send_parts_down = []
        send_parts_up = []

        for key in keys:
            if hasattr(self, "is_unicode_key") and self.write_script.is_unicode_key(key):
                send_parts_down.append(f'{{" Chr({ord(key)}) " down}}')
                send_parts_up.insert(0, f'{{" Chr({ord(key)}) " up}}')
            else:
                tr_key = self.write_script.translate_key(key)
                send_parts_down.append(f'{{{tr_key} down}}')
                send_parts_up.insert(0, f'{{{tr_key} up}}')

        send_sequence = "".join(send_parts_down + send_parts_up)
        file.write(f'{default_translated}::SendInput("{send_sequence}")\n')

    def write_single_key_remap(self, file, default_translated, remap_key):
        "Write single key case on remap key"
        if self.write_script.is_unicode_key(remap_key):
            file.write(f'{default_translated}::SendInput Chr({ord(remap_key)})\n')
        else:
            remap_key_tr = self.write_script.translate_key(remap_key)
            file.write(f'{default_translated}::{remap_key_tr}\n')

    def write_double_click(self, file, single_key, remap_key):
        "Write double click (same key twice) on default key"
        translated_key = self.write_script.translate_key(single_key)

        file.write(f'*{translated_key}::{{\n')
        file.write(
            (f'    if (A_PriorHotkey = "*{translated_key}") '
                'and (A_TimeSincePriorHotkey < 400)\n'
            )
        )

        if self.remap_widget.text_format_checkbox.isChecked():
            file.write(f'        SendText("{remap_key}")\n')
        elif self.remap_widget.hold_format_checkbox.isChecked():
            self.hold_format_double_click(remap_key, file)
        else:
            if "+" in remap_key:
                keys = [key.strip() for key in remap_key.split("+")]
                send_parts_down = []
                send_parts_up = []

                for key in keys:
                    if (hasattr(self, "is_unicode_key") and
                            self.write_script.is_unicode_key(key)):
                        send_parts_down.append(f'{{" Chr({ord(key)}) " down}}')
                        send_parts_up.insert(0, f'{{" Chr({ord(key)}) " up}}')
                    else:
                        tr_key = self.write_script.translate_key(key)
                        send_parts_down.append(f'{{{tr_key} down}}')
                        send_parts_up.insert(0, f'{{{tr_key} up}}')

                send_sequence = "".join(send_parts_down + send_parts_up)
                file.write(f'        SendInput("{send_sequence}")\n')
            else:
                if (hasattr(self, "is_unicode_key") and
                        self.write_script.is_unicode_key(remap_key)):
                    file.write(f'        Send Chr({ord(remap_key)})\n')
                else:
                    remap_key_tr = self.write_script.translate_key(remap_key)
                    file.write(f'        SendInput("{remap_key_tr}")\n')

        file.write('    }\n')

    def hold_format_double_click(self, remap_key, file):
        "Write double click on hold format"
        hold_interval_ms = "10000"
        if (self.remap_widget.hold_format_checkbox.isChecked()
            and self.remap_widget.hold_interval_entry is not None):
            hold_interval = "10"
            if (self.remap_widget.hold_interval_entry.text().strip() and
                self.remap_widget.hold_interval_entry.text().strip()
                    != "Hold Interval"):
                hold_interval = self.remap_widget. hold_interval_entry.text().strip()
            hold_interval_ms = str(int(float(hold_interval) * 1000))

        keys = [key.strip() for key in remap_key.split("+")]
        down_parts = []
        up_parts = []

        for key in keys:
            if (hasattr(self, "is_unicode_key") and
                    self.write_script.is_unicode_key(key)):
                down_parts.append(f'{{" Chr({ord(key)}) " Down}}')
                up_parts.insert(0, f'{{" Chr({ord(key)}) " Up}}')
            else:
                tr_key = self.write_script.translate_key(key)
                down_parts.append(f'{{{tr_key} Down}}')
                up_parts.insert(0, f'{{{tr_key} Up}}')

        down_sequence = "".join(down_parts)
        up_sequence = "".join(up_parts)

        file.write(
            (f'        (SendInput("{down_sequence}"), '
                f'SetTimer(() => SendInput("{up_sequence}"), -{hold_interval_ms}))\n'
            )
        )

    def write_multiple_key_default(self, default_key):
        "Write multiple key case on default key"
        if (self.remap_widget.first_key_checkbox is not None
            and self.remap_widget.first_key_checkbox.isChecked()):
            translated_key = self.write_script.translate_key(default_key)
        else:
            translated_key = "~" + self.write_script.translate_key(default_key)
        return translated_key

    def write_single_key_default(self, default_key):
        "Write single key case on default key"
        translated_key = self.write_script.translate_key(default_key)
        return translated_key
