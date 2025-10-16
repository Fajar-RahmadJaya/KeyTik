import os
import json
import random
import traceback
from PySide6.QtWidgets import (QMessageBox)
from PySide6.QtGui import QIcon
from utility.constant import (exit_keys_file, icon_path)
from utility.utils import (active_dir, store_dir)


class WriteScript:
    def generate_exit_key(self, script_name, file=None):
        possible_keys = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', # noqa
                        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'] # noqa

        try:
            if os.path.exists(exit_keys_file):
                try:
                    with open(exit_keys_file, 'r', encoding='utf-8') as f:
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
            with open(exit_keys_file, 'w', encoding='utf-8') as f:
                json.dump(exit_keys, f)

            if file is not None:
                file.write(f"{exit_combo}::ExitApp\n\n")

            return exit_combo

        except Exception as e:
            print(f"Error handling exit key: {e}")
            if file is not None:
                file.write("^!p::ExitApp\n\n")
            return "^!p"

    def initialize_exit_keys(self):
        try:
            ahk_files = set()
            for dir_path in [active_dir, store_dir]:
                if os.path.exists(dir_path):
                    ahk_files.update(
                        f for f in os.listdir(dir_path) if f.endswith('.ahk')
                    )

            exit_keys = {}
            if os.path.exists(exit_keys_file):
                try:
                    with open(exit_keys_file, 'r', encoding='utf-8') as f:
                        exit_keys = json.load(f)
                except Exception:
                    exit_keys = {}

            combo_to_scripts = {}
            for script, combo in exit_keys.items():
                combo_to_scripts.setdefault(combo, []).append(script)
            possible_keys = list('abcdefghijklmnopqrstuvwxyz')
            used_keys = set()
            for combo, scripts in combo_to_scripts.items():
                if len(scripts) == 1:
                    used_keys.add(combo[-1:])
                else:
                    used_keys.add(combo[-1:])
                    for script in scripts[1:]:
                        available_keys = [k for k in possible_keys
                                          if k not in used_keys]
                        if not available_keys:
                            available_keys = possible_keys
                        new_key = random.choice(available_keys)
                        used_keys.add(new_key)
                        exit_keys[script] = f"^!{new_key}"

            keys_to_remove = [k for k in exit_keys if k not in ahk_files]
            for k in keys_to_remove:
                del exit_keys[k]

            for script_name in ahk_files:
                if (script_name not in exit_keys
                    or exit_keys[script_name][-1]
                    in [exit_keys[s][-1]
                        for s in exit_keys
                        if s != script_name]):
                    possible_keys = list('abcdefghijklmnopqrstuvwxyz')
                    used_keys = set(exit_keys[s][-1]
                                    for s in exit_keys
                                    if s != script_name)
                    available_keys = [k for k in possible_keys
                                      if k not in used_keys]
                    if not available_keys:
                        available_keys = possible_keys
                    new_key = random.choice(available_keys)
                    exit_keys[script_name] = f"^!{new_key}"
                exit_combo = exit_keys[script_name]

                for dir_path in [active_dir, store_dir]:
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
                        except Exception as e:
                            print(f"Error processing {script_name} in {dir_path}: {e}") # noqa
                            continue

            try:
                with open(exit_keys_file, 'w', encoding='utf-8') as f:
                    json.dump(exit_keys, f)
            except Exception as e:
                print(f"Error saving exit_keys.json: {e}")

        except Exception as e:
            print(f"Error in initialize_exit_keys: {e}")

    def check_key_integrity(self, shortcut_types, caps_on_present, caps_off_present, num_on_present, num_off_present): # noqa
        if shortcut_types["normal"] and shortcut_types["caps"]:
            msg = (QMessageBox(self.edit_window
                               if hasattr(self, "edit_window")
                               else None))
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use 'CapsLock On' or 'CapsLock Off' or 'NumLock On' or 'Numlock Off' together with normal keys as shortcuts. Please use only one type (either normal keys or CapsLock NumLock ON/OFF) for all shortcuts.") # noqa
            msg.setWindowIcon(QIcon(icon_path))
            msg.exec()
            return False
        if caps_on_present and caps_off_present:
            msg = (QMessageBox(self.edit_window
                               if hasattr(self, "edit_window")
                               else None))
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use both 'CapsLock ON' and 'CapsLock OFF' at the same time. Please use only one of of them. If you need both, just use 'Caps Lock'.") # noqa
            msg.setWindowIcon(QIcon(icon_path))
            msg.exec()
            return False
        if num_on_present and num_off_present:
            msg = (QMessageBox(self.edit_window
                               if hasattr(self, "edit_window")
                               else None))
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use both 'NumLock ON' and 'NumLock OFF' at the same time. Please use only one of of them. If you need both, just use 'Caps Lock'.") # noqa
            msg.setWindowIcon(QIcon(icon_path))
            msg.exec()
            return False
        return True

    def save_changes(self, script_name):
        script_name = self.get_script_name()
        if not script_name:
            return

        shortcut_types = {"normal": [], "caps": []}
        caps_on_present = False
        caps_off_present = False
        num_on_present = False
        num_off_present = False
        for shortcut_row in self.shortcut_rows:
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
        if not self.check_key_integrity(shortcut_types, caps_on_present,
                                        caps_off_present, num_on_present,
                                        num_off_present):
            return

        output_path = os.path.join(self.SCRIPT_DIR, script_name)
        key_translations = self.load_key_translations()

        try:
            mode = None
            if hasattr(self, "mode_combobox"):
                mode = self.mode_combobox.currentText().strip().lower()
            self.is_text_mode = (mode == "text mode")

            with open(output_path, 'w', encoding='utf-8') as file:
                if mode == "text mode":
                    self.handle_text_mode(file, key_translations)
                elif mode == "default mode":
                    self.handle_default_mode(file, key_translations)
                else:
                    self.handle_default_mode(file, key_translations)

            self.scripts = self.list_scripts()
            self.update_script_list()
            self.edit_window.destroy()

        except Exception as e:
            print(f"Error writing script: {e}")
            traceback.print_exc()

    def get_program_condition(self):
        program_entry = self.program_entry.text().strip()
        program_condition = ""

        if program_entry:
            program_parts = program_entry.split(",")
            conditions = []

            for part in program_parts:
                part = part.strip()
                if part.lower().startswith("process"):
                    process_name = part.split("-")[1].strip()
                    conditions.append(f'WinActive("ahk_exe {process_name}")')
                elif part.lower().startswith("class"):
                    class_name = part.split("-")[1].strip()
                    conditions.append(f'WinActive("ahk_class {class_name}")')

            program_condition = " || ".join(conditions)

        return program_condition

    def get_device_condition(self):
        device_condition = ""
        device_name = self.keyboard_entry.text().strip()
        if device_name:
            device_condition = "cm1.IsActive"
        return device_condition

    def write_condition(self, file, key_translations, write_shortcuts=True,
                        write_program=True, write_device=True):
        device = self.keyboard_entry.text().strip() if write_device else None
        program = self.get_program_condition() if write_program else None
        shortcuts = None
        if write_shortcuts:
            shortcuts = [
                shortcut_row[0].text().strip()
                for shortcut_row in self.shortcut_rows
                if self.is_widget_valid(shortcut_row)
                and shortcut_row[0].text().strip()
            ] or None

        device_condition = None
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
            file.write("#include AutoHotkey Interception\\Lib\\AutoHotInterception.ahk\n\n") # noqa
            file.write("AHI := AutoHotInterception()\n")
            file.write(f"id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, {vid_pid_or_handle})\n") # noqa
            file.write("cm1 := AHI.CreateContextManager(id1)\n\n")
            device_condition = "cm1.IsActive"

        hotif_conditions = []
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
                        translated_shortcut = self.translate_key(
                            shortcut, key_translations)
                        file.write(f"~{translated_shortcut}:: ; Shortcuts\n")
                        file.write("{\n    global toggle\n    toggle := !toggle\n}\n\n") # noqa
                    hotif_conditions.append("toggle")
                elif caps_shortcuts:
                    hotif_conditions.append(" || ".join(caps_shortcuts))

        if program:
            hotif_conditions.append(f"({program})")

        if device_condition:
            hotif_conditions.append(device_condition)

        if hotif_conditions:
            file.write(f"#HotIf {' && '.join(hotif_conditions)}\n")
            return True
        return False

    def handle_default_mode(self, file, key_translations):
        file.write("; default\n")
        self.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")
        file.write("#Requires AutoHotkey v2.0\n")

        write_hotif = self.write_condition(file, key_translations,
                                           write_shortcuts=True,
                                           write_program=True,
                                           write_device=True)

        self.process_key_remaps(file, key_translations)

        if write_hotif:
            file.write("#HotIf\n")

    def handle_text_mode(self, file, key_translations):
        file.write("; text\n")
        self.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")
        file.write("#Requires AutoHotkey v2.0\n")

        write_hotif = self.write_condition(file, key_translations,
                                           write_shortcuts=True,
                                           write_program=True,
                                           write_device=True)

        text_content = self.text_block.toPlainText().strip()
        if text_content:
            file.write("; Text mode start\n")
            file.write(text_content + '\n')
            file.write("; Text mode end\n")

        if write_hotif:
            file.write("#HotIf\n")

    def process_key_remaps(self, file, key_translations):
        for row in self.key_rows:
            if len(row) >= 7:
                (default_key_entry, remap_key_entry, _,
                 _, text_format_var, hold_format_var,
                 hold_interval_entry) = row
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
                            file, keys[0], remap_key, key_translations,
                            text_format_var.isChecked(),
                            hold_format_var.isChecked(),
                            hold_format_var,
                            hold_interval_entry
                        )
                        continue
                    default_translated = self.write_multiple_key_default(
                        file, default_key, key_translations)

                else:
                    default_translated = self.write_single_key_default(
                        file, default_key, key_translations)

                self.handle_remap_type(
                    file, default_translated, remap_key, key_translations,
                    text_format_var.isChecked(),
                    hold_format_var.isChecked(),
                    hold_format_var,
                    hold_interval_entry,
                    has_multiple_keys
                )

            except Exception:
                continue

    def handle_remap_type(self, file, default_translated, remap_key,
                          key_translations, is_text_mode, is_hold_mode,
                          hold_format_var, hold_interval_entry,
                          has_multiple_keys):
        if is_text_mode:
            self.write_text_format(file, default_translated, remap_key)
        elif is_hold_mode:
            self.write_hold_format(
                file, default_translated, remap_key,
                key_translations, hold_format_var,
                hold_interval_entry, has_multiple_keys
            )
        elif "+" in remap_key:
            self.write_multiple_key_remap(file, default_translated,
                                          remap_key, key_translations)
        else:
            self.write_single_key_remap(file, default_translated,
                                        remap_key, key_translations)

    def write_single_key_default(self, file, default_key, key_translations):
        translated_key = self.translate_key(default_key, key_translations)
        return translated_key

    def write_single_key_remap(self, file, default_translated, remap_key,
                               key_translations):
        if hasattr(self, "is_unicode_key") and self.is_unicode_key(remap_key):
            file.write(f'{default_translated}::SendInput Chr({ord(remap_key)})\n') # noqa
        else:
            remap_key_tr = self.translate_key(remap_key, key_translations)
            file.write(f'{default_translated}::{remap_key_tr}\n')

    def write_multiple_key_default(self, file, default_key, key_translations):
        translated_key = "~" + self.translate_key(
            default_key, key_translations)
        return translated_key

    def write_multiple_key_remap(self, file, default_translated, remap_key,
                                 key_translations):
        keys = [key.strip() for key in remap_key.split("+")]
        send_parts_down = []
        send_parts_up = []

        for key in keys:
            if hasattr(self, "is_unicode_key") and self.is_unicode_key(key):
                send_parts_down.append(f'{{" Chr({ord(key)}) " down}}')
                send_parts_up.insert(0, f'{{" Chr({ord(key)}) " up}}')
            else:
                tr_key = self.translate_key(key, key_translations)
                send_parts_down.append(f'{{{tr_key} down}}')
                send_parts_up.insert(0, f'{{{tr_key} up}}')

        send_sequence = "".join(send_parts_down + send_parts_up)
        file.write(f'{default_translated}::SendInput("{send_sequence}")\n')

    def write_double_click(self, file, single_key, remap_key,
                           key_translations, is_text_mode, is_hold_mode,
                           hold_format_var, hold_interval_entry):
        translated_key = self.translate_key(single_key, key_translations)

        file.write(f'*{translated_key}::{{\n')
        file.write(f'    if (A_PriorHotkey = "*{translated_key}") and (A_TimeSincePriorHotkey < 400) {{\n') # noqa

        if is_text_mode:
            file.write(f'        SendText("{remap_key}")\n')
        elif is_hold_mode:
            hold_interval_ms = "10000"
            if hold_format_var.isChecked() and hold_interval_entry is not None:
                hold_interval = "10"
                if (hold_interval_entry.text().strip() and
                    hold_interval_entry.text().strip()
                        != "Hold Interval"):
                    hold_interval = hold_interval_entry.text().strip()
                hold_interval_ms = str(int(float(hold_interval) * 1000))

            keys = [key.strip() for key in remap_key.split("+")]
            down_parts = []
            up_parts = []

            for key in keys:
                if (hasattr(self, "is_unicode_key") and
                        self.is_unicode_key(key)):
                    down_parts.append(f'{{" Chr({ord(key)}) " Down}}')
                    up_parts.insert(0, f'{{" Chr({ord(key)}) " Up}}')
                else:
                    tr_key = self.translate_key(key, key_translations)
                    down_parts.append(f'{{{tr_key} Down}}')
                    up_parts.insert(0, f'{{{tr_key} Up}}')

            down_sequence = "".join(down_parts)
            up_sequence = "".join(up_parts)

            file.write(f'        (SendInput("{down_sequence}"), SetTimer(() => SendInput("{up_sequence}"), -{hold_interval_ms}))\n') # noqa

        else:
            if "+" in remap_key:
                keys = [key.strip() for key in remap_key.split("+")]
                send_parts_down = []
                send_parts_up = []

                for key in keys:
                    if (hasattr(self, "is_unicode_key") and
                            self.is_unicode_key(key)):
                        send_parts_down.append(f'{{" Chr({ord(key)}) " down}}')
                        send_parts_up.insert(0, f'{{" Chr({ord(key)}) " up}}')
                    else:
                        tr_key = self.translate_key(key, key_translations)
                        send_parts_down.append(f'{{{tr_key} down}}')
                        send_parts_up.insert(0, f'{{{tr_key} up}}')

                send_sequence = "".join(send_parts_down + send_parts_up)
                file.write(f'        SendInput("{send_sequence}")\n')
            else:
                if (hasattr(self, "is_unicode_key") and
                        self.is_unicode_key(remap_key)):
                    file.write(f'        Send Chr({ord(remap_key)})\n')
                else:
                    remap_key_tr = self.translate_key(
                        remap_key, key_translations)
                    file.write(f'        SendInput("{remap_key_tr}")\n')

        file.write('    }\n')
        file.write('}\n')

    def write_text_format(self, file, default_translated, remap_key):
        file.write(f'{default_translated}::SendText("{remap_key}")\n')

    def write_hold_format(self, file, default_translated, remap_key,
                          key_translations, hold_format_var,
                          hold_interval_entry, is_multiple_keys):
        hold_interval_ms = "10000"
        if hold_format_var.isChecked() and hold_interval_entry is not None:
            hold_interval = "10"
            if (hold_interval_entry.text().strip() and
                hold_interval_entry.text().strip()
                    != "Hold Interval"):
                hold_interval = hold_interval_entry.text().strip()
            hold_interval_ms = str(int(float(hold_interval) * 1000))

        keys = [key.strip() for key in remap_key.split("+")]
        down_parts = []
        up_parts = []

        for key in keys:
            if hasattr(self, "is_unicode_key") and self.is_unicode_key(key):
                down_parts.append(f'{{" Chr({ord(key)}) " Down}}')
                up_parts.insert(0, f'{{" Chr({ord(key)}) " Up}}')
            else:
                tr_key = self.translate_key(key, key_translations)
                down_parts.append(f'{{{tr_key} Down}}')
                up_parts.insert(0, f'{{{tr_key} Up}}')

        down_sequence = "".join(down_parts)
        up_sequence = "".join(up_parts)

        if "&" in default_translated:
            file.write(f'{default_translated}::(SendInput("{down_sequence}"), SetTimer(() => SendInput("{up_sequence}"), -{hold_interval_ms}))\n') # noqa
        else:
            file.write(f'*{default_translated}::(SendInput("{down_sequence}"), SetTimer(() => SendInput("{up_sequence}"), -{hold_interval_ms}))\n') # noqa
