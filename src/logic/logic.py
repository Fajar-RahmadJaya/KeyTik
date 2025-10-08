import os
import winshell
from win32com.client import Dispatch
import win32gui
import win32process
import json
from utility.constant import (script_dir, keylist_path)


class Logic:
    def list_scripts(self):
        all_scripts = [f for f in os.listdir(self.SCRIPT_DIR)
                       if f.endswith('.ahk') or f.endswith('.py')]

        pinned = [script for script in all_scripts
                  if script in self.pinned_profiles]
        unpinned = [script for script in all_scripts
                    if script not in self.pinned_profiles]

        self.scripts = pinned + unpinned
        return self.scripts

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_script_list()

    def next_page(self):
        if (self.current_page + 1) * 6 < len(self.scripts):
            self.current_page += 1
            self.update_script_list()

    def add_ahk_to_startup(self, script_name):
        script_path = os.path.join(self.SCRIPT_DIR, script_name)

        startup_folder = winshell.startup()

        shortcut_name = os.path.splitext(script_name)[0]
        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = script_path
        shortcut.WorkingDirectory = os.path.dirname(script_path)
        shortcut.IconLocation = script_path
        shortcut.save()

        del shell

        self.update_script_list()
        return shortcut_path

    def remove_ahk_from_startup(self, script_name):
        shortcut_name = os.path.splitext(script_name)[0]
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, f"{shortcut_name}.lnk")

        try:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                print(f"Removed {shortcut_path} from startup.")
            else:
                print(f"{shortcut_path} does not exist in startup.")

            self.update_script_list()

        except Exception as e:
            print(f"Error removing {shortcut_path}: {e}")

    def parse_device_info(self, file_path):
        devices = []
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()

            lines = [line.strip() for line in lines if line.strip()]

            device_info = {}
            for line in lines:
                line = line.strip()
                if line.startswith("Device ID"):
                    if device_info:
                        if (device_info.get('VID') and
                                device_info.get('PID') and
                                device_info.get('Handle')):
                            devices.append(device_info)
                    device_info = {'Device ID': line.split(":")[1].strip()}
                elif line.startswith("VID:"):
                    device_info['VID'] = line.split(":")[1].strip()
                elif line.startswith("PID:"):
                    device_info['PID'] = line.split(":")[1].strip()
                elif line.startswith("Handle:"):
                    device_info['Handle'] = line.split(":")[1].strip()
                elif line.startswith("Is Mouse:"):
                    device_info['Is Mouse'] = line.split(":")[1].strip()

            if (device_info.get('VID') and
                    device_info.get('PID') and
                    device_info.get('Handle')):
                devices.append(device_info)

        except Exception as e:
            print(f"Error reading device info: {e}")

        return devices

    def is_visible_application(self, pid):
        try:
            def callback(hwnd, pid_list):
                _, process_pid = win32process.GetWindowThreadProcessId(hwnd)
                if process_pid == pid and win32gui.IsWindowVisible(hwnd):
                    pid_list.append(pid)

            visible_pids = []
            win32gui.EnumWindows(callback, visible_pids)
            return len(visible_pids) > 0
        except Exception:
            return False

    def run_monitor(self):
        script_path = os.path.join(script_dir, "_internal", "Data", "Active",
                                   "AutoHotkey Interception", "Monitor.ahk")
        if os.path.exists(script_path):
            os.startfile(script_path)
        else:
            print(f"Error: The script at {script_path} does not exist.")

    def load_key_translations(self):
        key_translations = {}
        try:
            with open(keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key, info in keys.items():
                            readable_key = key.strip().lower()
                            translation = info.get("translate", "").strip()
                            if translation:
                                key_translations[readable_key] = translation

        except Exception as e:
            print(f"Error reading key translations: {e}")
        return key_translations

    def translate_key(self, key, key_translations):
        keys = key.split('+')
        translated_keys = []

        for single_key in keys:
            translated_key = key_translations.get(single_key.strip().lower(),
                                                  single_key.strip())
            translated_keys.append(translated_key)

        return " & ".join(translated_keys)

    def load_key_list(self):
        key_map = {}
        try:
            with open(keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key, info in keys.items():
                            readable = key
                            raw = info.get("translate", "")
                            if raw:
                                key_map[raw] = readable
        except Exception as e:
            print(f"Error reading key list: {e}")
        return key_map

    def load_key_values(self):
        key_values = []
        try:
            with open(keylist_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for category_dict in data:
                    for _, keys in category_dict.items():
                        for key in keys.keys():
                            key_values.append(key)
        except Exception as e:
            print(f"Error reading key_list.json: {e}")
        return key_values
