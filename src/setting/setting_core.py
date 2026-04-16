"Setting non UI code"

import os
import shutil
import webbrowser
import json
import subprocess
import ctypes
import requests
from PySide6.QtWidgets import (QMessageBox, QFileDialog)  # pylint: disable=E0611

from utility import constant
from utility import utils
from utility.diff import Diff, CHECK_UPDATE_LINK


class SettingCore():
    "Setting logic"
    def change_data_location(self, parent):
        "Change active and stored profile directory for 'change profile location'"
        # To Do: fix known issue.
        # Known issue: After successfully change data location, show stored not works
        new_path = QFileDialog.getExistingDirectory(
            parent, "Select a New Path for Active and Store Folders"
        )

        if not new_path:
            print("No directory selected. Operation canceled.")
            return

        try:
            if not os.path.exists(new_path):
                print(f"The selected path does not exist: {new_path}")
                return

            new_active_dir = os.path.join(new_path, 'Active')
            new_store_dir = os.path.join(new_path, 'Store')

            if os.path.exists(utils.active_dir):
                shutil.move(utils.active_dir, new_path)
                print(f"Moved Active folder to {new_path}")
            else:
                print(f"Active folder does not exist at {utils.active_dir}")

            if os.path.exists(utils.store_dir):
                shutil.move(utils.store_dir, new_path)
                print(f"Moved Store folder to {new_path}")
            else:
                print(f"Store folder does not exist at {utils.store_dir}")

            new_condition_data = {"path": new_path}
            with open(constant.condition_path, 'w', encoding='utf-8') as f:
                json.dump(new_condition_data, f)
            print(f"Updated condition.json with the new path: {new_path}")

            utils.active_dir = new_active_dir
            utils.store_dir = new_store_dir
            print(f"Global active_dir updated to: {utils.active_dir}")
            print(f"Global store_dir updated to: {utils.store_dir}")

            QMessageBox.information(
                None, "Change Profile Location",
                "Profile location changed successfully!")
        except PermissionError as e:
            print(f"An error occurred: {e}")
            QMessageBox.critical(None, "Error", f"An error occurred: {e}")

    def save_theme(self, theme):
        "Write theme preference to theme file"
        try:
            with open(constant.theme_path, 'w', encoding='utf-8') as f:
                if theme == "system":
                    f.write("")
                else:
                    f.write(theme)
        except FileNotFoundError:
            print("Error: theme_path file not found")

    def read_theme(self):
        "Read saved theme preference from theme file"
        try:
            if os.path.exists(constant.theme_path):
                with open(constant.theme_path, 'r', encoding= 'utf-8') as f:
                    theme = f.read().strip().lower()
                if theme in ("dark", "light"):
                    return theme
            return "system"
        except FileNotFoundError:
            print("Error: theme_path file not found")
            return "system"

    def ahk_action(self, ahk_installed):
        "Uninstall AutoHotkey"
        if ahk_installed:
            try:
                with subprocess.Popen(utils.ahk_uninstall_path, shell=True) as proc:
                    proc.wait()

            except FileNotFoundError:
                QMessageBox.critical(
                    None,
                    "Error", 
                    "Failed to uninstall: AutoHotkey installation path not found") 
        else:
            webbrowser.open("https://www.autohotkey.com")

    def driver_action(self, driver_installed):
        "Uninstall interception driver"
        try:
            if driver_installed:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas",
                    constant.interception_uninstall_path, None, None, 1
                )
            else:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", constant.interception_install_path,
                    None, None, 1
                )
        except FileNotFoundError:
            QMessageBox.critical(
                None,
                "Error", 
                "Failed to uninstall: inter_uninstall.bat not found") 

    def check_for_update(self):
        "Check for update comparing current version and latest version from GitHub API"
        diff = Diff()  # Composition
        try:
            response = requests.get(CHECK_UPDATE_LINK, timeout=5)
            if response.status_code == 200:
                return diff.parse_update_response(response)
        except requests.exceptions.ConnectionError:
            pass
        return None
