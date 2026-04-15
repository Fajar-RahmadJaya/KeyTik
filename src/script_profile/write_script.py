"Write AutoHotkey script"

from dataclasses import dataclass
import os
import json
import random
from PySide6.QtWidgets import (QLineEdit, QCheckBox)  # pylint: disable=E0611
from utility import constant

from utility import utils
from utility.diff import Diff
from core.main_core import MainCore
from select_key.select_key_core import SelectKeyCore


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
        # Composition
        self.diff = Diff()
        self.main_core = MainCore()
        self.select_key_core = SelectKeyCore()

        self.is_text_mode = None

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

    def process_key_remaps(self, file, remap_row):
        "Handle key remap write"
        for row in remap_row.key_rows:
            (default_key_entry, remap_key_entry, _,
            _, text_format_checkbox, hold_format_checkbox,
            hold_interval_entry, first_key_checkbox, _) = row

            remap_row.key_rows = KeyRows(
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
                            file, keys[0], remap_key, remap_row
                        )
                        continue
                    default_translated = self.write_multiple_key_default(default_key, remap_row)

                else:
                    default_translated = self.write_single_key_default(
                        default_key)

                self.handle_remap_type(file, default_translated, remap_key, remap_row)

            except ValueError:
                continue

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

        key_translations = self.load_key_translations()

        for single_key in keys:
            translated_key = key_translations.get(single_key.strip().lower(),
                                                    single_key.strip())
            translated_keys.append(translated_key)

        return " & ".join(translated_keys)


    def handle_remap_type(self, file, default_translated, remap_key, remap_row):
        "Handle text, hold, single, multiple key mode"
        if remap_row.key_rows.text_format_checkbox.isChecked():
            self.write_text_format(file, default_translated, remap_key)
        elif remap_row.key_rows.hold_format_checkbox.isChecked():
            self.write_hold_format(file, default_translated, remap_key, remap_row)
        elif "+" in remap_key:
            self.write_multiple_key_remap(file, default_translated,
                                          remap_key)
        else:
            self.write_single_key_remap(file, default_translated,
                                        remap_key)

    def write_single_key_default(self, default_key):
        "Write single key case on default key"
        translated_key = self.translate_key(default_key)
        return translated_key

    def is_unicode_key(self, key):
        "Determine whether it's unicode or hard coded key"
        key_data = self.select_key_core.load_keylist()
        for child_item in key_data.values():
            if key in child_item:
                return False
        return True

    def write_single_key_remap(self, file, default_translated, remap_key):
        "Write single key case on remap key"
        if self.is_unicode_key(remap_key):
            file.write(f'{default_translated}::SendInput Chr({ord(remap_key)})\n')
        else:
            remap_key_tr = self.translate_key(remap_key)
            file.write(f'{default_translated}::{remap_key_tr}\n')

    def write_multiple_key_default(self, default_key, remap_row):
        "Write multiple key case on default key"
        if (remap_row.key_rows.first_key_checkbox is not None
            and remap_row.key_rows.first_key_checkbox.isChecked()):
            translated_key = self.translate_key(default_key)
        else:
            translated_key = "~" + self.translate_key(default_key)
        return translated_key

    def write_multiple_key_remap(self, file, default_translated, remap_key):
        "Write multiple key case on remap key"
        keys = [key.strip() for key in remap_key.split("+")]
        send_parts_down = []
        send_parts_up = []

        for key in keys:
            if hasattr(self, "is_unicode_key") and self.is_unicode_key(key):
                send_parts_down.append(f'{{" Chr({ord(key)}) " down}}')
                send_parts_up.insert(0, f'{{" Chr({ord(key)}) " up}}')
            else:
                tr_key = self.translate_key(key)
                send_parts_down.append(f'{{{tr_key} down}}')
                send_parts_up.insert(0, f'{{{tr_key} up}}')

        send_sequence = "".join(send_parts_down + send_parts_up)
        file.write(f'{default_translated}::SendInput("{send_sequence}")\n')

    def write_double_click(self, file, single_key, remap_key, remap_row):
        "Write double click (same key twice) on default key"
        translated_key = self.translate_key(single_key)

        file.write(f'*{translated_key}::{{\n')
        file.write(
            (f'    if (A_PriorHotkey = "*{translated_key}") '
             'and (A_TimeSincePriorHotkey < 400)\n'
            )
        )

        if remap_row.key_rows.text_format_checkbox.isChecked():
            file.write(f'        SendText("{remap_key}")\n')
        elif remap_row.key_rows.hold_format_checkbox.isChecked():
            self.hold_format_double_click(remap_key, file, remap_row)
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
                        tr_key = self.translate_key(key)
                        send_parts_down.append(f'{{{tr_key} down}}')
                        send_parts_up.insert(0, f'{{{tr_key} up}}')

                send_sequence = "".join(send_parts_down + send_parts_up)
                file.write(f'        SendInput("{send_sequence}")\n')
            else:
                if (hasattr(self, "is_unicode_key") and
                        self.is_unicode_key(remap_key)):
                    file.write(f'        Send Chr({ord(remap_key)})\n')
                else:
                    remap_key_tr = self.translate_key(remap_key)
                    file.write(f'        SendInput("{remap_key_tr}")\n')

        file.write('    }\n')

    def hold_format_double_click(self, remap_key, file, remap_row):
        "Write double click on hold format"
        hold_interval_ms = "10000"
        if (remap_row.key_rows.hold_format_checkbox.isChecked()
            and remap_row.key_rows.hold_interval_entry is not None):
            hold_interval = "10"
            if (remap_row.key_rows.hold_interval_entry.text().strip() and
                remap_row.key_rows.hold_interval_entry.text().strip()
                    != "Hold Interval"):
                hold_interval =remap_row.key_rows. hold_interval_entry.text().strip()
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
                tr_key = self.translate_key(key)
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

    def write_hold_format(self, file, default_translated, remap_key, remap_row):
        "Write hold format"
        hold_interval_ms = "10000"
        if (remap_row.key_rows.hold_format_checkbox.isChecked()
            and remap_row.key_rows.hold_interval_entry is not None):
            hold_interval = "10"
            if (remap_row.key_rows.hold_interval_entry.text().strip() and
                remap_row.key_rows.hold_interval_entry.text().strip()
                    != "Hold Interval"):
                hold_interval = remap_row.key_rows.hold_interval_entry.text().strip()
            hold_interval_ms = str(int(float(hold_interval) * 1000))

        keys = [key.strip() for key in remap_key.split("+")]
        down_parts = []
        up_parts = []

        for key in keys:
            if hasattr(self, "is_unicode_key") and self.is_unicode_key(key):
                down_parts.append(f'{{" Chr({ord(key)}) " Down}}')
                up_parts.insert(0, f'{{" Chr({ord(key)}) " Up}}')
            else:
                tr_key = self.translate_key(key)
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
