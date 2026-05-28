"Setting non UI code"

import os
import shutil
import webbrowser
import subprocess
import ctypes
import requests
from PySide6.QtWidgets import QMessageBox, QFileDialog, QApplication  # pylint: disable=E0611
from PySide6.QtGui import QPalette  # pylint: disable=E0611

from keytik.utility import constant
from keytik.utility import utils
from keytik.utility import style
from keytik.utility import diff
from keytik.dashboard.dashboard_core import DashboardCore


class SettingCore:
    "Setting logic"

    def change_data_location(self, parent):
        "Change active and stored profile directory for 'change profile location'"
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

            # Save profile path to config
            config = utils.get_config()
            config.profile_path = new_path
            utils.update_config(config)

            print(f"Updated condition.json with the new path: {new_path}")

            utils.active_dir = new_active_dir
            utils.store_dir = new_store_dir
            print(f"Global active_dir updated to: {utils.active_dir}")
            print(f"Global store_dir updated to: {utils.store_dir}")

            # Reactive script after move profile successfully
            for script in running_scripts:
                dashboard_core.activate_script(script)

            QMessageBox.information(
                None,
                "Change Profile Location",
                "Profile location changed successfully!",
            )
        except PermissionError as e:
            print(f"An error occurred: {e}")
            QMessageBox.critical(None, "Error", f"An error occurred: {e}")

    def save_theme(self, theme: dict, parent):
        "Write theme preference to config file"
        try:
            config = utils.get_config()

            config.theme_type = theme.get("type")
            config.theme = theme.get("value")
            utils.update_config(config)

            # Apply palette directly when theme is in the same default color
            palette = style.get_palette()
            base_light = style.is_light(palette.color(QPalette.Base))
            default_theme_light = (
                os.environ.get("QT_QPA_PLATFORM") == "windows:darkmode=1"
            )

            # Palette with different default theme need restart
            if base_light != default_theme_light or theme.get("value") in (
                "light",
                "dark",
            ):
                QMessageBox.information(
                    parent,
                    "Success",
                    f"""Theme changed to {config.theme}.
Please restart {diff.PROGRAM_NAME} to apply change.""",
                )
            else:
                # Set palette
                QApplication.setPalette(palette)
                QApplication.setStyleSheet(
                    QApplication.instance(), style.button_highlight(style_sheet=True)
                )

        except FileNotFoundError as error:
            QMessageBox.critical(parent, "Error", f"Failed to change theme\n{error}")

    def save_accent(self, accent: list, parent):
        "Write accent preference to config file"
        try:
            config = utils.get_config()
            config.accent = accent[1]
            utils.update_config(config)

            # Update accent palette and button highlight stylesheet
            QApplication.setPalette(style.get_palette())
            QApplication.setStyleSheet(
                QApplication.instance(), style.button_highlight(style_sheet=True)
            )

        except FileNotFoundError as error:
            QMessageBox.critical(parent, "Error", f"Failed to change Accent\n{error}")

    def save_style(self, updated_style):
        "Write style preference to config file"
        try:
            config = utils.get_config()
            config.style = "" if updated_style == "Default" else updated_style
            utils.update_config(config)

            # Update style
            QApplication.setStyle(updated_style)

        except FileNotFoundError as error:
            print(f"Error: {error}")

    def save_mica_effect(self, new_mica, parent):
        "Write style preference to config file"
        try:
            config = utils.get_config()
            prev_mica = config.mica_effect

            # Update config
            config.mica_effect = new_mica.lower()
            utils.update_config(config)

            # setting widget to be translucent pr remove it need restart
            if prev_mica == "disable" or new_mica.lower() == "disable":
                QMessageBox.information(
                    parent,
                    "Success",
                    f"""Mica effect enabled.
Please restart {diff.PROGRAM_NAME} to apply change.""",
                )
            else:
                # Apply mica on setting window
                style.apply_mica(parent)
                # Apply mica on main window
                style.apply_mica(parent.window().parentWidget())

        except FileNotFoundError as error:
            QMessageBox.critical(parent, "Error", f"Failed to change style\n{error}")

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
                    "Failed to uninstall: AutoHotkey installation path not found",
                )
        else:
            webbrowser.open("https://www.autohotkey.com")

    def driver_action(self, driver_installed):
        "Uninstall interception driver"
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
                None, "Error", "Failed to uninstall: inter_uninstall.bat not found"
            )

    def check_for_update(self):
        "Check for update comparing current version and latest version from GitHub API"
        try:
            response = requests.get(diff.CHECK_UPDATE_LINK, timeout=5)
            if response.status_code == 200:
                return diff.parse_update_response(response)
        except requests.exceptions.ConnectionError:
            pass
        return None

    def get_custom_theme(self) -> list[str]:
        "Return list containing custom theme"
        theme_file = []

        for file in os.listdir(constant.theme_dir):
            theme_file.append(file)

        return theme_file
