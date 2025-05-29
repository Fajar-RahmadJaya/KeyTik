import os
import json
import random
import traceback  # <-- Add this import
from src.utility.constant import (exit_keys_file)
from src.utility.utils import (active_dir)

class EditScriptSave:
    def write_first_line(self, file):
        script_name = os.path.basename(file.name)
        exit_key = self.generate_exit_key(script_name)  # First get the key

        if self.is_text_mode:
            file.write("; text\n")
        else:
            file.write("; default\n")
        file.write(f"{exit_key}::ExitApp \n\n#SingleInstance Force\n")  # Then write it to file

    def generate_exit_key(self, script_name, file=None):
        """Generate random exit key combination, save to JSON, and optionally write to file"""
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
        """Initialize exit keys for all AHK scripts on startup"""
        try:
            # Check if exit_keys.json exists in data_dir
            if not os.path.exists(exit_keys_file):
                print("No exit_keys.json found. Generating exit keys for all scripts...")
                exit_keys = {}

                # Get all .ahk files in active_dir
                ahk_files = [f for f in os.listdir(active_dir) if f.endswith('.ahk')]

                for script_name in ahk_files:
                    script_path = os.path.join(active_dir, script_name)

                    try:
                        # Read first line to determine script type
                        with open(script_path, 'r', encoding='utf-8') as f:
                            first_line = f.readline().strip()
                            lines = f.readlines()

                        # Generate new random exit key
                        exit_combo = f"^!{random.choice('abcdefghijklmnopqrstuvwxyz')}"
                        exit_keys[script_name] = exit_combo


                        if first_line == "; default":
                            new_content = ["; default\n",
                                        f"{exit_combo}::ExitApp\n\n"]
                            new_content.extend(lines[2:])
                        elif first_line == "; text":
                            new_content = ["; text\n",
                                        f"{exit_combo}::ExitApp\n\n"]
                            new_content.extend(lines[2:])

                        # Write back updated content
                        with open(script_path, 'w', encoding='utf-8') as f:
                            f.writelines(new_content)

                    except Exception as e:
                        print(f"Error processing {script_name}: {e}")
                        continue

                # Save all exit keys to json
                try:
                    with open(exit_keys_file, 'w') as f:
                        json.dump(exit_keys, f)
                except Exception as e:
                    print(f"Error saving exit_keys.json: {e}")

            else:
                print("exit_keys.json found, using existing exit keys.")

        except Exception as e:
            print(f"Error in initialize_exit_keys: {e}")

    def handle_device(self, file):
        # Use .text() for QLineEdit instead of .get()
        keyboard_entry = self.keyboard_entry.text().strip()
        if keyboard_entry:
            parts = keyboard_entry.split(",", 1)
            device_type = parts[0].strip().lower()
            vid_pid_or_handle = parts[1].strip()

            if device_type == "mouse":
                is_mouse = True
            elif device_type == "keyboard":
                is_mouse = False
            else:
                raise ValueError(f"Unknown device type: {device_type}")

            if vid_pid_or_handle.startswith("0x"):
                vid, pid = vid_pid_or_handle.split(",")
                file.write(self.generate_device_code(is_mouse, vid.strip(), pid.strip()))
            else:
                file.write(self.generate_device_code_from_handle(is_mouse, vid_pid_or_handle))

    def generate_device_code(self, is_mouse, vid, pid):
        return f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceId({str(is_mouse).lower()}, {vid}, {pid})
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
"""

    def generate_device_code_from_handle(self, is_mouse, handle):
        return f"""#SingleInstance force
Persistent
#include AutoHotkey Interception\Lib\AutoHotInterception.ahk

AHI := AutoHotInterception()
id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, "{handle}")
cm1 := AHI.CreateContextManager(id1)

#HotIf cm1.IsActive
"""
    
    def save_changes(self, script_name):
        script_name = self.get_script_name()
        if not script_name:
            return

        output_path = os.path.join(self.SCRIPT_DIR, script_name)
        key_translations = self.load_key_translations()

        try:
            with open(output_path, 'w') as file:
                self.write_first_line(file)
                self.handle_device(file)

                program_condition = self.get_program_condition()
                device_condition = self.get_device_condition()
                # FIX: Use .currentText() for QComboBox instead of .get()
                shortcuts_present = any(
                    self.is_widget_valid(shortcut_row) and shortcut_row[0].currentText().strip()
                    for shortcut_row in self.shortcut_rows
                )

                if self.is_text_mode:
                    self.handle_text_mode(file, key_translations, program_condition, shortcuts_present,
                                        device_condition)
                else:
                    self.handle_default_mode(file, key_translations, program_condition, shortcuts_present,
                                            device_condition)
                
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