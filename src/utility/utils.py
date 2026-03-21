"Utility module"
import os
import json
import tempfile
import sys
import winreg
import utility.constant as constant


def load_condition():
    "Load condition for active and stored profile location"
    try:
        if os.path.exists(constant.condition_path):
            with open(constant.condition_path, "r", encoding="utf-8") as condition_file:
                content = condition_file.read().strip()
                if content:
                    data = json.loads(content)
                    if isinstance(data, dict) and "path" in data:
                        return data["path"]
                else:
                    print("Condition file is empty. Returning None.")
    except json.JSONDecodeError:
        print("Error: Condition file is not in valid JSON format.") # noqa
    except FileNotFoundError as e:
        print(f"Error: {e}")
    return None


path_from_condition = load_condition()


if path_from_condition:
    active_dir = os.path.join(path_from_condition, 'Active')
    store_dir = os.path.join(path_from_condition, 'Store')
else:

    active_dir = os.path.join(constant.appdata_dir, 'Active')
    store_dir = os.path.join(constant.appdata_dir, 'Store')


if not os.path.exists(active_dir):
    os.makedirs(active_dir)

if not os.path.exists(store_dir):
    os.makedirs(store_dir)


SCRIPT_DIR = active_dir


def load_pinned_profiles():
    "Load file storing pinned profile"
    try:
        if os.path.exists(constant.pinned_file):
            with open(constant.pinned_file, "r", encoding="utf-8") as pin_file:
                content = pin_file.read().strip()
                if content:
                    data = json.loads(content)
                    if isinstance(data, list):
                        return data
                else:
                    print("Pinned profiles file is empty. Returning an empty list.") # noqa
    except json.JSONDecodeError:
        print("Error: Pinned profiles file is not in valid JSON format.") # noqa
    except FileNotFoundError as e:
        print(f"Error: {e}")
    return []


def save_pinned_profiles(pinned_profiles):
    "Write pin profile to file"
    with open(constant.pinned_file, "w", encoding="utf-8") as pin_file:
        json.dump(pinned_profiles, pin_file)


if not os.path.exists(constant.appdata_dir):
    os.makedirs(constant.appdata_dir)


if not os.path.exists(constant.condition_path):
    with open(constant.condition_path, "w", encoding="utf-8") as f:
        json.dump({"path": ""}, f)


if not os.path.exists(constant.pinned_file):
    with open(constant.pinned_file, "w", encoding="UTF-8") as f:
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
    "Read temp to store running script"
    scripts = set()
    if os.path.exists(TEMP_RUNNING_FILE):
        try:
            with open(TEMP_RUNNING_FILE, "r", encoding="utf-8") as run_file:
                scripts = set(line.strip() for line in run_file if line.strip())
        except FileNotFoundError as e:
            print(f"Error: {e}")
    return scripts


def write_running_scripts_temp(scripts):
    "Write temp to store running script"
    try:
        with open(TEMP_RUNNING_FILE, "w", encoding="utf-8") as run_file:
            for s in scripts:
                run_file.write(s + "\n")
    except FileNotFoundError as e:
        print(f"Error: {e}")


def add_script_to_temp(script_name):
    "Add running script to temp"
    scripts = read_running_scripts_temp()
    scripts.add(script_name)
    write_running_scripts_temp(scripts)


def remove_script_from_temp(script_name):
    "Remove running script to temp"
    scripts = read_running_scripts_temp()
    scripts.discard(script_name)
    write_running_scripts_temp(scripts)


def detect_system_theme():
    "Detecting system theme for Pyside6 default theme handling"
    if sys.platform == "win32":
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            theme_registry = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            key = winreg.OpenKey(registry, theme_registry) # noqa
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "dark" if value == 0 else "light"
        except FileNotFoundError:
            print("Theme registry not found.")
    return "light"

def get_theme():
    "Get user theme preference"
    try:
        if os.path.exists(constant.theme_path):
            with open(constant.theme_path, 'r', encoding="utf-8") as theme_file:
                theme_pref = theme_file.read().strip().lower()
            if theme_pref in ("dark", "light"):
                return theme_pref
        return detect_system_theme()
    except FileNotFoundError:
        return detect_system_theme()


theme = get_theme()


def get_ahk_install_dir():
    "Get AutoHotkey installation directory in case not installed via other method"
    reg_paths = [
        r"SOFTWARE\AutoHotkey",
        r"SOFTWARE\WOW6432Node\AutoHotkey"
    ]
    for reg_path in reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                return install_dir
        except FileNotFoundError:
            continue
    return None

ahk_uninstall_path = os.path.join(get_ahk_install_dir() or r"C:\Program Files\AutoHotkey\UX\ui-uninstall.ahk", "UX", "ui-uninstall.ahk") # noqa # pylint: disable=C0301,E0401
ahkv2_dir = os.path.join(get_ahk_install_dir() or r"C:\Program Files\AutoHotkey", "v2") # noqa
