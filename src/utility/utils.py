"Utility module"

import os
import json
from dataclasses import dataclass
import winreg


from utility import constant


# ------------------------------ Migrate Old Config ------------------------------
def migrate_old_config():
    "Move old config to new centralized one"
    try:
        config_structure = {
            "show_announcement": load_show_announcement(),
            "theme": load_theme(),
            "profile_path": load_profile_path(),
            "pinned_profile": load_pinned_profile(),
            "exit_key": load_exit_key(),
        }
        with open(constant.config_path, "w", encoding="utf-8") as config_file:
            json.dump(config_structure, config_file, indent=4, sort_keys=True)
    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")


def load_profile_path():
    "Load old config profile path"
    try:
        condition_path = os.path.join(constant.appdata_dir, "path.json")
        with open(condition_path, "r", encoding="utf-8") as condition_file:
            value = json.load(condition_file)
            profile_path = value.get("path", constant.appdata_dir)
        os.remove(condition_path)
    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
        profile_path = constant.appdata_dir

    return profile_path


def load_theme():
    "Load old config theme"
    try:
        theme_path = os.path.join(constant.appdata_dir, "theme.json")
        with open(theme_path, "r", encoding="utf-8") as theme_file:
            theme = theme_file.read().strip().lower()
        os.remove(theme_path)
    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
        theme = None

    return theme


def load_show_announcement():
    "Load old config show announcement"
    try:
        show_announcement_path = os.path.join(constant.appdata_dir, "dont_show.json")
        with open(show_announcement_path, "r", encoding="utf-8") as dont_show_file:
            value = json.load(dont_show_file)
            show_announcement = value.get("welcome_condition", True)
        os.remove(show_announcement_path)
    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
        show_announcement = True

    return show_announcement


def load_pinned_profile():
    "Load old config pinned profile"
    try:
        pinned_profile_path = os.path.join(constant.appdata_dir, "pinned_profiles.json")
        with open(pinned_profile_path, "r", encoding="utf-8") as pin_file:
            pinned_profile = json.load(pin_file)
        os.remove(pinned_profile_path)
    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
        pinned_profile = []

    return pinned_profile


def load_exit_key():
    "Load old config exit key"
    try:
        exit_keys_path = os.path.join(constant.appdata_dir, "exit_keys.json")
        with open(exit_keys_path, "r", encoding="utf-8") as exit_key_file:
            exit_key = json.load(exit_key_file)
        os.remove(exit_keys_path)
    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
        exit_key = {}

    return exit_key


# ------------------------------ Config ------------------------------
@dataclass
class Config:  # pylint: disable=R0902
    "Dataclass to make config usage easier"

    show_announcement: bool
    style: str
    theme_type: str
    theme: dict
    accent: str
    mica_effect: str
    profile_path: str
    pinned_profile: list
    exit_key: dict


def get_config():
    "Get config from json file"
    if not os.path.exists(constant.config_path):
        migrate_old_config()

    try:
        with open(constant.config_path, "r", encoding="utf-8") as config_file:
            value = json.load(config_file)
            config = Config(
                show_announcement=value.get("show_announcement", True),
                style=value.get("style") or None,
                theme_type=value.get("theme_type") or "default",
                theme=value.get("theme") or "system",
                accent=value.get("accent") or "default",
                mica_effect=value.get("mica_effect") or "default",
                profile_path=value.get("profile_path") or constant.appdata_dir,
                pinned_profile=value.get("pinned_profile", []),
                exit_key=value.get("exit_key", {}),
            )
        return config

    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
    return None


def update_config(config):
    "Save config into json file"
    try:
        with open(constant.config_path, "w", encoding="utf-8") as f:
            json.dump(config.__dict__, f, indent=4, sort_keys=True)
    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")


active_dir = os.path.join(get_config().profile_path, "Active")
store_dir = os.path.join(get_config().profile_path, "Store")

if not os.path.exists(active_dir):
    os.makedirs(active_dir)

if not os.path.exists(store_dir):
    os.makedirs(store_dir)

if not os.path.exists(constant.appdata_dir):
    os.makedirs(constant.appdata_dir)

device_list_path = os.path.join(
    active_dir, "Autohotkey Interception", "shared_device_info.txt"
)
device_finder_path = os.path.join(
    active_dir, "Autohotkey Interception", "find_device.ahk"
)
coordinate_path = os.path.join(active_dir, "Autohotkey Interception", "Coordinate.ahk")


def get_ahk_install_dir():
    "Get AutoHotkey installation directory in case not installed via other method"
    reg_paths = [r"SOFTWARE\AutoHotkey", r"SOFTWARE\WOW6432Node\AutoHotkey"]
    for reg_path in reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                return install_dir
        except FileNotFoundError:
            continue
    return None


ahk_uninstall_path = os.path.join(
    get_ahk_install_dir() or r"C:\Program Files\AutoHotkey\UX\ui-uninstall.ahk",
    "UX",
    "ui-uninstall.ahk",
)
ahkv2_dir = os.path.join(get_ahk_install_dir() or r"C:\Program Files\AutoHotkey", "v2")
