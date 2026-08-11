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

"""Setting non UI code."""

import ctypes
import os
import shutil
import subprocess
import sys
import webbrowser

import requests
from PySide6.QtGui import QPalette  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QApplication,
    QFileDialog,
    QMessageBox,
)

from keytik.dashboard.dashboard_core import DashboardCore
from keytik.utility import constant
from keytik.utility.style import Palette, Styling
from keytik.utility.utils import Config, Utility


class SettingCore:
    """Setting logic."""

    def __init__(self):
        self.utility = Utility()

    def restart_app(self):
        """Run new instance and remove the old one."""
        try:
            subprocess.Popen([sys.executable, *sys.argv], close_fds=True)  # pylint: disable=R1732
            sys.exit(0)
        except (OSError, ValueError) as error:
            print(error)

    def change_data_location(self, parent):
        """Change active and stored profile directory for 'change profile location'."""
        new_path = QFileDialog.getExistingDirectory(
            parent, "Select a New Path for Active and Store Folders"
        )

        if not new_path:
            print("No directory selected. Operation canceled.")
            return

        dashboard_core = DashboardCore()

        try:
            # Exit all script first to prevent administrator issue
            running_scripts = dashboard_core.get_running_ahk()
            for script in running_scripts:
                dashboard_core.exit_script(script_name=script)

            if not os.path.exists(new_path):
                print(f"The selected path does not exist: {new_path}")
                return

            new_active_dir = os.path.join(new_path, "Active")
            new_store_dir = os.path.join(new_path, "Store")

            if os.path.exists(self.utility.active_dir):
                shutil.move(self.utility.active_dir, new_path)
                print(f"Moved Active folder to {new_path}")
            else:
                print(f"Active folder does not exist at {self.utility.active_dir}")

            if os.path.exists(self.utility.store_dir):
                shutil.move(self.utility.store_dir, new_path)
                print(f"Moved Store folder to {new_path}")
            else:
                print(f"Store folder does not exist at {self.utility.store_dir}")

            # Save profile path to config
            config = Config().get_config()
            config.profile_path = new_path
            Config().update_config(config)

            print(f"Updated condition.json with the new path: {new_path}")

            self.utility.active_dir = new_active_dir
            self.utility.store_dir = new_store_dir
            print(f"Global active_dir updated to: {self.utility.active_dir}")
            print(f"Global store_dir updated to: {self.utility.store_dir}")

            # Reactive script after move profile successfully
            for script in running_scripts:
                dashboard_core.activate_script(script)

            QMessageBox.information(
                QApplication.activeWindow(),
                "Change Profile Location",
                "Profile location changed successfully!",
            )
        except PermissionError as e:
            print(f"An error occurred: {e}")
            QMessageBox.critical(QApplication.activeWindow(), "Error", f"An error occurred: {e}")

    def save_theme(self, theme: dict, parent):
        """Write theme preference to config file."""
        try:
            config = Config().get_config()

            config.theme_type = theme.get("type")
            config.theme = theme.get("value")
            Config().update_config(config)

            # Apply palette directly when theme is in the same default color
            palette_comp = Palette()
            palette = palette_comp.get_palette()
            base_light = palette_comp.is_light(palette.color(QPalette.Base))
            default_theme_light = os.environ.get("QT_QPA_PLATFORM") == "windows:darkmode=1"

            # Palette with different default theme need restart
            if base_light != default_theme_light or theme.get("value") in (
                "light",
                "dark",
            ):
                messagebox = QMessageBox(parent)
                messagebox.setIcon(QMessageBox.Icon.Information)
                messagebox.setWindowTitle("Success")
                messagebox.setText(
                    f"Theme changed to {config.theme}. "
                    f"Please restart {self.utility.program_name} to apply change.\n\n"
                    f"Would you like to restart {self.utility.program_name}?",
                )
                messagebox.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                response = messagebox.exec()
                if response == QMessageBox.StandardButton.Yes:
                    self.restart_app()
            else:
                # Set palette
                QApplication.setPalette(palette)
                QApplication.setStyleSheet(
                    QApplication.instance(), Styling().button_highlight(style_sheet=True)
                )

        except FileNotFoundError as error:
            QMessageBox.critical(parent, "Error", f"Failed to change theme\n{error}")

    def save_accent(self, accent: list, parent):
        """Write accent preference to config file."""
        try:
            config = Config().get_config()
            config.accent = accent[1]
            Config().update_config(config)

            # Update accent palette and button highlight stylesheet
            QApplication.setPalette(Palette().get_palette())
            QApplication.setStyleSheet(
                QApplication.instance(), Styling().button_highlight(style_sheet=True)
            )

        except FileNotFoundError as error:
            QMessageBox.critical(parent, "Error", f"Failed to change Accent\n{error}")

    def save_style(self, updated_style):
        """Write style preference to config file."""
        try:
            config = Config().get_config()
            config.style = "" if updated_style == "Default" else updated_style
            Config().update_config(config)

            # Update style
            QApplication.setStyle(updated_style)

        except FileNotFoundError as error:
            print(f"Error: {error}")

    def save_mica_effect(self, new_mica, parent):
        """Write style preference to config file."""
        try:
            config = Config().get_config()
            prev_mica = config.mica_effect

            # Update config
            config.mica_effect = new_mica.lower()
            Config().update_config(config)

            if prev_mica == "disable" or new_mica.lower() == "disable":
                messagebox = QMessageBox(parent)
                messagebox.setIcon(QMessageBox.Icon.Information)
                messagebox.setWindowTitle("Success")
                messagebox.setText(
                    f"Mica effect changed to {new_mica}. "
                    f"Please restart {self.utility.program_name} to apply change.\n\n"
                    f"Would you like to restart {self.utility.program_name}?",
                )
                messagebox.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                response = messagebox.exec()
                if response == QMessageBox.StandardButton.Yes:
                    self.restart_app()
            else:
                styling = Styling()
                # Apply mica on setting window
                styling.apply_mica(parent)
                # Apply mica on main window
                styling.apply_mica(parent.window().parentWidget())

        except FileNotFoundError as error:
            QMessageBox.critical(parent, "Error", f"Failed to change style\n{error}")

    def save_auto_complete(self, new_auto_complete):
        """Write auto complete preferences preference to config file."""
        try:
            config = Config().get_config()

            # Update config
            config.auto_complete = new_auto_complete
            Config().update_config(config)

        except FileNotFoundError as error:
            print(f"Error: {error}")

    def save_enable_peek(self, is_enabled: bool, parent):
        """Write peek script preferences to config file."""
        try:
            config_comp = Config()
            config = config_comp.get_config()

            # Update config
            config.enable_peek = is_enabled
            config_comp.update_config(config)

            messagebox = QMessageBox(parent)
            messagebox.setIcon(QMessageBox.Icon.Information)
            messagebox.setWindowTitle("Success")
            messagebox.setText(
                f"Peek script {'enabled' if is_enabled else 'disabled'}. "
                f"Please restart {self.utility.program_name} to apply change.\n\n"
                f"Would you like to restart {self.utility.program_name}?",
            )
            messagebox.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            response = messagebox.exec()
            if response == QMessageBox.StandardButton.Yes:
                self.restart_app()

        except FileNotFoundError as error:
            print(f"Error: {error}")

    def ahk_action(self, ahk_installed):
        """Uninstall AutoHotkey."""
        ahk_uninstall_path = os.path.join(
            self.utility.get_ahk_install_dir() or r"C:\Program Files\AutoHotkey",
            "UX",
            "ui-uninstall.ahk",
        )

        if ahk_installed:
            try:
                subprocess.run(ahk_uninstall_path, shell=True, check=True)

            except FileNotFoundError:
                QMessageBox.critical(
                    QApplication.activeWindow(),
                    "Error",
                    "Failed to uninstall: AutoHotkey installation path not found",
                )
        else:
            webbrowser.open("https://www.autohotkey.com")

    def driver_action(self, driver_installed):
        """Uninstall interception driver."""
        try:
            if driver_installed:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", constant.interception_uninstall_path, None, None, 1
                )
            else:
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", constant.interception_install_path, None, None, 1
                )
        except FileNotFoundError:
            QMessageBox.critical(
                QApplication.activeWindow(),
                "Error",
                "Failed to uninstall: inter_uninstall.bat not found",
            )

    def get_custom_theme(self) -> list[str]:
        """Return list containing custom theme."""
        theme_file = []

        for file in os.listdir(constant.theme_dir):
            theme_file.append(file)

        return theme_file

    def get_unreleased_changlog(self) -> str:
        """Get unreleased changelog generated by Git-Cliff action."""
        try:
            success_code = 200
            unreleased_link = (
                "https://raw.githubusercontent.com/Fajar-RahmadJaya/KeyTik/changelog/CHANGELOG.md"
            )

            response = requests.get(unreleased_link, timeout=5)
            if response.status_code == success_code:
                unreleased_version, unreleased_changelog_md = response.text.split("\n", 1)
                unreleased_version = unreleased_version.replace("## KeyTik", "")
                unreleased_version = unreleased_version.replace("Preview", "")

                return unreleased_version.strip(), unreleased_changelog_md

        except requests.exceptions.ConnectionError:
            pass
        return "Failed to fetch unreleased changelog."
