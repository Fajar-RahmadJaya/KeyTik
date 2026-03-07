import os
import shutil
from PySide6.QtWidgets import (
    QMessageBox, QFileDialog, QInputDialog
)
import webbrowser
import json
import subprocess
import ctypes
import utility.constant as constant
import utility.utils as utils
from utility.diff import Diff


class SettingComponent(Diff):
    def change_data_location(self):
        global active_dir, store_dir

        new_path = QFileDialog.getExistingDirectory(
            self, "Select a New Path for Active and Store Folders"
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

            if os.path.exists(active_dir):
                shutil.move(active_dir, new_path)
                print(f"Moved Active folder to {new_path}")
            else:
                print(f"Active folder does not exist at {active_dir}")

            if os.path.exists(store_dir):
                shutil.move(store_dir, new_path)
                print(f"Moved Store folder to {new_path}")
            else:
                print(f"Store folder does not exist at {store_dir}")

            new_condition_data = {"path": new_path}
            with open(constant.condition_path, 'w') as f:
                json.dump(new_condition_data, f)
            print(f"Updated condition.json with the new path: {new_path}")

            active_dir = new_active_dir
            store_dir = new_store_dir
            print(f"Global active_dir updated to: {active_dir}")
            print(f"Global store_dir updated to: {store_dir}")

            self.SCRIPT_DIR = active_dir
            self.scripts = self.list_scripts()
            self.update_script_list()

            QMessageBox.information(
                self, "Change Profile Location",
                "Profile location changed successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def check_update_and_show_messagebox(self):
        latest_version = self.check_for_update()
        self.update_messagebox(latest_version, show_no_update_message=True)

    def change_theme_dialog(self):
        options = ["Light", "Dark", "System"]
        current_theme = self.read_theme()
        if current_theme == "dark":
            current_index = 1
        elif current_theme == "light":
            current_index = 0
        else:
            current_index = 2
        theme, ok = QInputDialog.getItem(
            self, "Change Theme", "Select theme:",
            options, current_index, False)
        if ok:
            self.save_theme(theme.lower())
            QMessageBox.information(self, "Theme Changed", "Theme will be applied after restarting the app.") # noqa

    def read_theme(self):
        try:
            if os.path.exists(constant.theme_path):
                with open(constant.theme_path, 'r') as f:
                    theme = f.read().strip().lower()
                if theme in ("dark", "light"):
                    return theme
            return "system"
        except Exception:
            return "system"

    def save_theme(self, theme):
        try:
            with open(constant.theme_path, 'w') as f:
                if theme == "system":
                    f.write("")
                else:
                    f.write(theme)
        except Exception as e:
            print(f"Failed to save theme: {e}")

    def ahk_action(slf, ahk_installed, dialog):
        if ahk_installed:
            try:
                subprocess.Popen(utils.ahk_uninstall_path, shell=True)
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to start uninstall: {e}") # noqa
        else:
            webbrowser.open("https://www.autohotkey.com")

    def driver_action(self, driver_installed, dialog):
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
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Failed to run driver installer/uninstaller: {e}") # noqa
