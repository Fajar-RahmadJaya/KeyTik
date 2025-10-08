import os
import json
import tempfile
import sys
from utility.constant import (appdata_dir, pinned_file, condition_path,
                              theme_path)


def load_condition():
    try:
        if os.path.exists(condition_path):
            with open(condition_path, "r") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    if isinstance(data, dict) and "path" in data:
                        return data["path"]
                else:
                    print("Condition file is empty. Returning None.")
    except json.JSONDecodeError:
        print("Error: Condition file is not in valid JSON format. Resetting condition.") # noqa
    except Exception as e:
        print(f"An error occurred while loading condition: {e}")
    return None


path_from_condition = load_condition()


if path_from_condition:
    active_dir = os.path.join(path_from_condition, 'Active')
    store_dir = os.path.join(path_from_condition, 'Store')
else:

    active_dir = os.path.join(appdata_dir, 'Active')
    store_dir = os.path.join(appdata_dir, 'Store')


if not os.path.exists(active_dir):
    os.makedirs(active_dir)

if not os.path.exists(store_dir):
    os.makedirs(store_dir)


SCRIPT_DIR = active_dir


def load_pinned_profiles():
    try:
        if os.path.exists(pinned_file):
            with open(pinned_file, "r") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    if isinstance(data, list):
                        return data
                else:
                    print("Pinned profiles file is empty. Returning an empty list.") # noqa
    except json.JSONDecodeError:
        print("Error: Pinned profiles file is not in valid JSON format. Resetting pinned profiles.") # noqa
    except Exception as e:
        print(f"An error occurred while loading pinned profiles: {e}")
    return []


def save_pinned_profiles(pinned_profiles):
    with open(pinned_file, "w") as f:
        json.dump(pinned_profiles, f)


if not os.path.exists(appdata_dir):
    os.makedirs(appdata_dir)


if not os.path.exists(condition_path):
    with open(condition_path, "w") as f:
        json.dump({"path": ""}, f)


if not os.path.exists(pinned_file):
    with open(pinned_file, "w") as f:
        json.dump([
            "Multiple Files Opener.ahk",
            "Take Coordinate And Copy It For Screen Clicker.ahk",
            "Screen Clicker.ahk",
            "Auto Clicker.ahk"
        ], f)

device_list_path = os.path.join(
    active_dir, "Autohotkey Interception", "shared_device_info.txt")
device_finder_path = os.path.join(
    active_dir, "Autohotkey Interception", "find_device.ahk")
coordinate_path = os.path.join(
    active_dir, "Autohotkey Interception", "Coordinate.ahk")

TEMP_RUNNING_FILE = os.path.join(tempfile.gettempdir(), "running_scripts.tmp")


def read_running_scripts_temp():
    scripts = set()
    if os.path.exists(TEMP_RUNNING_FILE):
        try:
            with open(TEMP_RUNNING_FILE, "r", encoding="utf-8") as f:
                scripts = set(line.strip() for line in f if line.strip())
        except Exception as e:
            print(f"[read_running_scripts_temp] Error: {e}")
    return scripts


def write_running_scripts_temp(scripts):
    try:
        with open(TEMP_RUNNING_FILE, "w", encoding="utf-8") as f:
            for s in scripts:
                f.write(s + "\n")
    except Exception as e:
        print(f"[write_running_scripts_temp] Error: {e}")


def add_script_to_temp(script_name):
    scripts = read_running_scripts_temp()
    scripts.add(script_name)
    write_running_scripts_temp(scripts)


def remove_script_from_temp(script_name):
    scripts = read_running_scripts_temp()
    scripts.discard(script_name)
    write_running_scripts_temp(scripts)


def detect_system_theme():
    if sys.platform == "win32":
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") # noqa
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "dark" if value == 0 else "light"
        except Exception:
            return "light"


def get_theme():
    try:
        if os.path.exists(theme_path):
            with open(theme_path, 'r') as f:
                theme = f.read().strip().lower()
            if theme in ("dark", "light"):
                return theme
        return detect_system_theme()
    except Exception:
        return detect_system_theme()


theme = get_theme()
