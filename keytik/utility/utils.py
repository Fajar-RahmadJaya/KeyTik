# Copyright 2024 Fajar Rahmad Jaya
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility module."""

import json
import os
import winreg
from dataclasses import dataclass

from keytik.utility import constant


# ------------------------------ Config ------------------------------
@dataclass
class ConfigData:  # pylint: disable=R0902
    """Dataclass to make config usage easier."""

    show_announcement: bool
    style: str
    theme_type: str
    theme: dict
    accent: str
    mica_effect: str
    profile_path: str
    pinned_profile: list
    exit_key: dict
    auto_complete: str
    skip_update: str


class Config:
    """Program config."""

    def get_config(self):
        """Get config from json file."""
        if not os.path.exists(constant.config_path):
            self.migrate_old_config()

        try:
            with open(constant.config_path, encoding="utf-8") as config_file:
                value = json.load(config_file)
                config = ConfigData(
                    show_announcement=value.get("show_announcement", True),
                    style=value.get("style") or None,
                    theme_type=value.get("theme_type") or "default",
                    theme=value.get("theme") or "system",
                    accent=value.get("accent") or "default",
                    mica_effect=value.get("mica_effect") or "default",
                    profile_path=value.get("profile_path") or constant.appdata_dir,
                    pinned_profile=value.get("pinned_profile", []),
                    exit_key=value.get("exit_key", {}),
                    auto_complete=value.get("auto_complete") or "inline",
                    skip_update=value.get("skip_update") or None,
                )
            return config

        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")
        return None

    def update_config(self, config):
        """Save config into json file."""
        try:
            with open(constant.config_path, "w", encoding="utf-8") as f:
                json.dump(config.__dict__, f, indent=4, sort_keys=True)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")

    # ------------------------------ Migrate Old Config ------------------------------
    def migrate_old_config(self):
        """Move old config to new centralized one."""
        try:
            config_structure = {
                "show_announcement": self.load_show_announcement(),
                "theme": self.load_theme(),
                "profile_path": self.load_profile_path(),
                "pinned_profile": self.load_pinned_profile(),
                "exit_key": self.load_exit_key(),
            }
            with open(constant.config_path, "w", encoding="utf-8") as config_file:
                json.dump(config_structure, config_file, indent=4, sort_keys=True)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")

    def load_profile_path(self):
        """Load old config profile path."""
        try:
            condition_path = os.path.join(constant.appdata_dir, "path.json")
            with open(condition_path, encoding="utf-8") as condition_file:
                value = json.load(condition_file)
                profile_path = value.get("path", constant.appdata_dir)
            os.remove(condition_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")
            profile_path = constant.appdata_dir

        return profile_path

    def load_theme(self):
        """Load old config theme."""
        try:
            theme_path = os.path.join(constant.appdata_dir, "theme.json")
            with open(theme_path, encoding="utf-8") as theme_file:
                theme = theme_file.read().strip().lower()
            os.remove(theme_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")
            theme = None

        return theme

    def load_show_announcement(self):
        """Load old config show announcement."""
        try:
            show_announcement_path = os.path.join(constant.appdata_dir, "dont_show.json")
            with open(show_announcement_path, encoding="utf-8") as dont_show_file:
                value = json.load(dont_show_file)
                show_announcement = value.get("welcome_condition", True)
            os.remove(show_announcement_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")
            show_announcement = True

        return show_announcement

    def load_pinned_profile(self):
        """Load old config pinned profile."""
        try:
            pinned_profile_path = os.path.join(constant.appdata_dir, "pinned_profiles.json")
            with open(pinned_profile_path, encoding="utf-8") as pin_file:
                pinned_profile = json.load(pin_file)
            os.remove(pinned_profile_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")
            pinned_profile = []

        return pinned_profile

    def load_exit_key(self):
        """Load old config exit key."""
        try:
            exit_keys_path = os.path.join(constant.appdata_dir, "exit_keys.json")
            with open(exit_keys_path, encoding="utf-8") as exit_key_file:
                exit_key = json.load(exit_key_file)
            os.remove(exit_keys_path)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")
            exit_key = {}

        return exit_key


# ------------------------------ Data ------------------------------
@dataclass
class Datas:  # pylint: disable=R0902
    """Dataclass to make data usage easier."""

    latest_update_check: str
    latest_version: str
    changelog: str


class Data:
    """Program data."""

    def get_data(self):
        """Get config from json file."""
        data_path = constant.data_path
        if not os.path.exists(data_path):
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

        try:
            with open(data_path, encoding="utf-8") as data_file:
                value = json.load(data_file)
                data = Datas(
                    latest_update_check=value.get("latest_update_check", True),
                    latest_version=value.get("latest_version") or None,
                    changelog=value.get("changelog") or None,
                )
            return data

        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")
        return None

    def update_data(self, data: Datas):
        """Save data into json file."""
        try:
            with open(constant.data_path, "w", encoding="utf-8") as f:
                json.dump(data.__dict__, f, indent=4, sort_keys=True)
        except (json.JSONDecodeError, FileNotFoundError) as error:
            print(f"Error: {error}")


# ------------------------------ Metadata ------------------------------
def get_metadata():
    """Get program metadata.."""
    try:
        with open(constant.meta_path, encoding="utf-8") as data_file:
            value = json.load(data_file)
            name = value.get("name", "KeyTik")
            version = value.get("version") or "Unknown"
        return name, version

    except (json.JSONDecodeError, FileNotFoundError) as error:
        print(f"Error: {error}")
    return "KeyTik", "Unknown"


program_name, current_version = get_metadata()

active_dir = os.path.join(Config().get_config().profile_path, "Active")
store_dir = os.path.join(Config().get_config().profile_path, "Store")

if not os.path.exists(active_dir):
    os.makedirs(active_dir)

if not os.path.exists(store_dir):
    os.makedirs(store_dir)

if not os.path.exists(constant.appdata_dir):
    os.makedirs(constant.appdata_dir)


def get_ahk_install_dir():
    """Get AutoHotkey installation directory in case not installed via other method."""
    reg_paths = [r"SOFTWARE\AutoHotkey", r"SOFTWARE\WOW6432Node\AutoHotkey"]
    for reg_path in reg_paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                return install_dir
        except FileNotFoundError:
            continue
    return None


ahkv2_dir = os.path.join(get_ahk_install_dir() or r"C:\Program Files\AutoHotkey", "v2")
