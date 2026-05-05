"Utility module"
import os
import json
import sys
import winreg
from PySide6.QtCore import QRect, Qt  # pylint: disable=E0611
import win32mica

from utility import constant

# ------------------------------ Config ------------------------------
def load_condition():
    "Load condition for active and stored profile location"
    try:
        with open(constant.condition_path, "r", encoding="utf-8") as condition_file:
            content = condition_file.read().strip()
            if content:
                data = json.loads(content)
                if isinstance(data, dict) and "path" in data:
                    return data["path"]
            else:
                return constant.appdata_dir

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: {e}")
    return None

def get_theme():
    "Get user theme preference"
    try:
        if os.path.exists(constant.theme_path):
            with open(constant.theme_path, 'r', encoding="utf-8") as theme_file:
                theme_pref = theme_file.read().strip().lower()
            return theme_pref

    except FileNotFoundError as error:
        print(f"Error: {error}")
    return detect_system_theme()

theme = get_theme()  # Cache

def load_announcement_condition():
    "Load user preference from file, whether to show announcement or not"
    try:
        with open(constant.dont_show_path, "r", encoding='utf-8') as file:
            config = json.load(file)
            return config.get("welcome_condition", True)

    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
    return True

def load_pinned_profiles():
    "Load file storing pinned profile"
    try:
        with open(constant.pinned_file, "r", encoding="utf-8") as pin_file:
            content = pin_file.read().strip()
            if content:
                data = json.loads(content)
                if isinstance(data, list):
                    return data

    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
    return []

def load_exit_keys():
    "Load file storing exit keys for each profile"
    try:
        with open(constant.exit_keys_file, 'r', encoding='utf-8') as file:
            exit_keys = json.load(file)
        return exit_keys

    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
    return {}

active_dir = os.path.join(load_condition(), 'Active')
store_dir = os.path.join(load_condition(), 'Store')

if not os.path.exists(active_dir):
    os.makedirs(active_dir)

if not os.path.exists(store_dir):
    os.makedirs(store_dir)

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

def detect_system_theme():
    "Detecting system theme for Pyside6 default theme handling"
    if sys.platform == "win32":
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            theme_registry = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            key = winreg.OpenKey(registry, theme_registry)
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "dark" if value == 0 else "light"
        except FileNotFoundError:
            print("Theme registry not found.")
    return "light"

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

ahk_uninstall_path = os.path.join(
    get_ahk_install_dir()
    or r"C:\Program Files\AutoHotkey\UX\ui-uninstall.ahk",
    "UX",
    "ui-uninstall.ahk")
ahkv2_dir = os.path.join(get_ahk_install_dir() or r"C:\Program Files\AutoHotkey", "v2")

def get_geometry(parent_window, width, height):
    "Get x and y centered relative to parent window"
    parent_geometry = parent_window.geometry()
    parent_x = parent_geometry.x()
    parent_y = parent_geometry.y()
    parent_width = parent_geometry.width()
    parent_height = parent_geometry.height()

    x = parent_x + (parent_width - width) // 2
    y = parent_y + (parent_height - height) // 2
    return QRect(x, y, width, height)

def apply_mica(target_window):
    "Apply mica style on target window using win32mica"
    target_window.setAttribute(Qt.WA_TranslucentBackground)
    win32mica.ApplyMica(
        HWND=int(target_window.winId()),
        Theme=win32mica.MicaTheme.AUTO,
        Style=win32mica.MicaStyle.DEFAULT)
