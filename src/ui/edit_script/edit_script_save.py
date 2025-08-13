import os
import json
import random
import traceback  
from PySide6.QtWidgets import (
    QComboBox, QSpinBox, QRadioButton, QGroupBox, QFrame, QMessageBox
)
from PySide6.QtGui import QIcon  # <-- Add this import
from src.utility.constant import (exit_keys_file, icon_path)  # <-- Add icon_path
from src.utility.utils import (active_dir, store_dir)

class EditScriptSave:
    def generate_exit_key(self, script_name, file=None):
        possible_keys = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

        try:
            # Load existing exit keys
            if os.path.exists(exit_keys_file):
                try:
                    with open(exit_keys_file, 'r') as f:
                        exit_keys = json.load(f)
                except json.JSONDecodeError:
                    # If JSON is invalid, start fresh
                    exit_keys = {}
            else:
                exit_keys = {}

            # Get all currently used keys
            used_keys = set(key[-1] for key in exit_keys.values())
            available_keys = [k for k in possible_keys if k not in used_keys]

            if not available_keys:  # If all keys are used (unlikely with 26 options)
                available_keys = possible_keys

            # Generate unique exit combo
            exit_combo = f"^!{random.choice(available_keys)}"  # Ctrl+Alt+RandomKey

            # Save to JSON
            exit_keys[script_name] = exit_combo
            with open(exit_keys_file, 'w') as f:
                json.dump(exit_keys, f)

            # If file object is provided, write the exit key to it
            if file is not None:
                file.write(f"{exit_combo}::ExitApp\n\n")

            return exit_combo

        except Exception as e:
            print(f"Error handling exit key: {e}")
            if file is not None:
                file.write("^!p::ExitApp\n\n")  # Fallback to default if writing to file
            return "^!p"  # Return default if error

    def initialize_exit_keys(self):
        try:
            # Gather all .ahk files from both active_dir and store_dir
            ahk_files = set()
            for dir_path in [active_dir, store_dir]:
                if os.path.exists(dir_path):
                    ahk_files.update(
                        f for f in os.listdir(dir_path) if f.endswith('.ahk')
                    )

            # Load or create exit_keys_file
            exit_keys = {}
            if os.path.exists(exit_keys_file):
                try:
                    with open(exit_keys_file, 'r') as f:
                        exit_keys = json.load(f)
                except Exception:
                    exit_keys = {}

            # --- Ensure all exit keys are unique ---
            # Reverse mapping: exit_combo -> [script_names]
            combo_to_scripts = {}
            for script, combo in exit_keys.items():
                combo_to_scripts.setdefault(combo, []).append(script)
            possible_keys = list('abcdefghijklmnopqrstuvwxyz')
            used_keys = set()
            for combo, scripts in combo_to_scripts.items():
                if len(scripts) == 1:
                    used_keys.add(combo[-1:])
                else:
                    # Duplicate found, keep one, regenerate for the rest
                    used_keys.add(combo[-1:])
                    for script in scripts[1:]:
                        # Find an unused key
                        available_keys = [k for k in possible_keys if k not in used_keys]
                        if not available_keys:
                            available_keys = possible_keys
                        new_key = random.choice(available_keys)
                        used_keys.add(new_key)
                        exit_keys[script] = f"^!{new_key}"

            # Remove keys for scripts that no longer exist
            keys_to_remove = [k for k in exit_keys if k not in ahk_files]
            for k in keys_to_remove:
                del exit_keys[k]

            # Add missing keys and update scripts' second line
            for script_name in ahk_files:
                # If missing, generate a new exit key (ensure uniqueness)
                if script_name not in exit_keys or exit_keys[script_name][-1] in [exit_keys[s][-1] for s in exit_keys if s != script_name]:
                    possible_keys = list('abcdefghijklmnopqrstuvwxyz')
                    used_keys = set(exit_keys[s][-1] for s in exit_keys if s != script_name)
                    available_keys = [k for k in possible_keys if k not in used_keys]
                    if not available_keys:
                        available_keys = possible_keys
                    new_key = random.choice(available_keys)
                    exit_keys[script_name] = f"^!{new_key}"
                exit_combo = exit_keys[script_name]

                # Update the script file in both dirs if present
                for dir_path in [active_dir, store_dir]:
                    script_path = os.path.join(dir_path, script_name)
                    if os.path.exists(script_path):
                        try:
                            with open(script_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                            # Ensure at least two lines
                            if len(lines) < 2:
                                lines += ['\n'] * (2 - len(lines))
                            # Update the second line to the exit key
                            lines[1] = f"{exit_combo}::ExitApp\n"
                            with open(script_path, 'w', encoding='utf-8') as f:
                                f.writelines(lines)
                        except Exception as e:
                            print(f"Error processing {script_name} in {dir_path}: {e}")
                            continue

            # Save all exit keys to json
            try:
                with open(exit_keys_file, 'w') as f:
                    json.dump(exit_keys, f)
            except Exception as e:
                print(f"Error saving exit_keys.json: {e}")

        except Exception as e:
            print(f"Error in initialize_exit_keys: {e}")
    
    def save_changes(self, script_name):
        script_name = self.get_script_name()
        if not script_name:
            return

        # --- BEGIN: Shortcut validation logic ---
        shortcut_types = {"normal": [], "caps": []}
        for shortcut_row in self.shortcut_rows:
            if self.is_widget_valid(shortcut_row):
                shortcut = shortcut_row[0].currentText().strip()
                if shortcut:
                    if shortcut.lower() in ["caps on", "caps off"]:
                        shortcut_types["caps"].append(shortcut)
                    else:
                        shortcut_types["normal"].append(shortcut)
        # If both normal and caps shortcuts are present, show error and abort
        if shortcut_types["normal"] and shortcut_types["caps"]:
            msg = QMessageBox(self.edit_window if hasattr(self, "edit_window") else None)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use 'Caps On' or 'Caps Off' together with normal keys as shortcuts. Please use only one type (either normal keys or Caps On/Off) for all shortcuts.")
            msg.setWindowIcon(QIcon(icon_path))
            msg.exec()
            return
        # --- END: Shortcut validation logic ---

        output_path = os.path.join(self.SCRIPT_DIR, script_name)
        key_translations = self.load_key_translations()

        try:
            # Determine mode from combobox if available
            mode = None
            if hasattr(self, "mode_combobox"):
                mode = self.mode_combobox.currentText().strip().lower()
            # --- Set is_text_mode according to combobox ---
            self.is_text_mode = (mode == "text mode")

            with open(output_path, 'w') as file:
                # Prefer mode from combobox if available
                if mode == "text mode":
                    self.handle_text_mode(file, key_translations)
                elif mode == "default mode":
                    self.handle_default_mode(file, key_translations)
                else:
                    self.handle_default_mode(file, key_translations)

            # Finalize and update script list
            self.scripts = self.list_scripts()
            self.update_script_list()
            self.edit_window.destroy()

        except Exception as e:
            print(f"Error writing script: {e}")
            traceback.print_exc()  # <-- Add this line for detailed error info

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
        device_name = self.keyboard_entry.text().strip()  # Retrieve device info from the entry
        if device_name:
            device_condition = f"cm1.IsActive"  # Modify this if needed to generate the correct condition
        return device_condition
    
    def write_condition(self, file, key_translations, write_shortcuts=True, write_program=True, write_device=True):
        device = self.keyboard_entry.text().strip() if write_device else None
        program = self.get_program_condition() if write_program else None
        shortcuts = None
        if write_shortcuts:
            shortcuts = [
                shortcut_row[0].currentText().strip()
                for shortcut_row in self.shortcut_rows
                if self.is_widget_valid(shortcut_row) and shortcut_row[0].currentText().strip()
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
            file.write(f"Persistent\n")
            file.write(f"#include AutoHotkey Interception\\Lib\\AutoHotInterception.ahk\n\n")
            file.write(f"AHI := AutoHotInterception()\n")
            file.write(f"id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, {vid_pid_or_handle})\n")
            file.write(f"cm1 := AHI.CreateContextManager(id1)\n\n")
            device_condition = "cm1.IsActive"

        hotif_conditions = []
        if shortcuts:
            valid_shortcuts = [s for s in shortcuts if s]
            if valid_shortcuts:
                caps_shortcuts = []
                normal_shortcuts = []
                for shortcut in valid_shortcuts:
                    if shortcut.lower() == "caps on":
                        caps_shortcuts.append('GetKeyState("CapsLock", "T")')
                    elif shortcut.lower() == "caps off":
                        caps_shortcuts.append('!GetKeyState("CapsLock", "T")')
                    else:
                        normal_shortcuts.append(shortcut)
                if normal_shortcuts:
                    file.write("toggle := false\n\n")
                    for shortcut in normal_shortcuts:
                        translated_shortcut = self.translate_key(shortcut, key_translations)
                        file.write(f"~{translated_shortcut}:: ; Shortcuts\n")
                        file.write("{\n    global toggle\n    toggle := !toggle\n}\n\n")
                    hotif_conditions.append("toggle")
                elif caps_shortcuts:
                    hotif_conditions.append(" || ".join(caps_shortcuts))

        if program:
            hotif_conditions.append(f"({program})")

        if device_condition:
            hotif_conditions.append(device_condition)

        if hotif_conditions:
            file.write(f"#HotIf {' && '.join(hotif_conditions)}\n")
            return True  # Indicate that #HotIf was written
        return False  # No #HotIf written
    
    def handle_default_mode(self, file, key_translations):
        file.write("; default\n")
        self.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")

        write_hotif = self.write_condition(file, key_translations, write_shortcuts=True, write_program=True, write_device=True)

        self.process_key_remaps(file, key_translations)

        # Close #HotIf for both program and device conditions only if written
        if write_hotif:
            file.write("#HotIf\n")

    def handle_text_mode(self, file, key_translations):
        file.write("; text\n")
        self.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")

        write_hotif = self.write_condition(file, key_translations, write_shortcuts=True, write_program=True, write_device=True)

        text_content = self.text_block.toPlainText().strip()
        if text_content:
            file.write("; Text mode start\n")
            file.write(text_content + '\n')
            file.write("; Text mode end\n")

        # Close #HotIf for both program and device conditions only if written
        if write_hotif:
            file.write("#HotIf\n")