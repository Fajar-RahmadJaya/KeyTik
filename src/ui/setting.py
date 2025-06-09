import os
import shutil
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QGroupBox, QPushButton, 
    QMessageBox, QFileDialog, QInputDialog
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import webbrowser
import requests
import json
from src.utility.constant import (current_version, icon_path, 
                                  condition_path, theme_path)
from src.utility.utils import (active_dir)

class Setting:
    def open_settings_window(self):
        # Create a new dialog window
        settings_window = QDialog(self)
        settings_window.setWindowTitle("Settings")
        settings_window.setGeometry(400, 225, 400, 300)
        settings_window.setWindowIcon(QIcon(icon_path))
        settings_window.setModal(True)
        settings_window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, getattr(self, "is_on_top", False))

        # Main layout
        main_layout = QVBoxLayout(settings_window)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Group box (equivalent to LabelFrame)
        group_box = QGroupBox()
        group_layout = QGridLayout(group_box)
        group_layout.setContentsMargins(10, 10, 10, 10)

        # Change Profile Location button
        change_path_button = QPushButton("Change Profile Location")
        change_path_button.setFixedHeight(40)
        change_path_button.setFixedWidth(180)
        change_path_button.clicked.connect(self.change_data_location)
        group_layout.addWidget(change_path_button, 0, 0, 1, 1)

        # Check For Update button
        check_update_button = QPushButton("Check For Update")
        check_update_button.setFixedHeight(40)
        check_update_button.setFixedWidth(180)
        check_update_button.clicked.connect(lambda: self.check_for_update(show_no_update_message=True))
        group_layout.addWidget(check_update_button, 0, 1, 1, 1)

        # On Boarding button
        readme_button = QPushButton("Readme!")
        readme_button.setFixedHeight(40)
        readme_button.setFixedWidth(180)
        readme_button.clicked.connect(self.show_welcome_window)
        group_layout.addWidget(readme_button, 1, 0, 1, 1)

        # Theme button now lets user pick theme
        theme_button = QPushButton("Change Theme")
        theme_button.setFixedHeight(40)
        theme_button.setFixedWidth(180)
        theme_button.clicked.connect(self.change_theme_dialog)
        group_layout.addWidget(theme_button, 1, 1, 1, 1)

        # Sponsor Me button
        pro_upgrade_button = QPushButton("Upgrade to KeyTik Pro")
        pro_upgrade_button.setFixedHeight(40)
        pro_upgrade_button.setFixedWidth(370)
        pro_upgrade_button.clicked.connect(lambda: webbrowser.open("https://fajarrahmadjaya.gumroad.com/l/keytik-pro"))
        group_layout.addWidget(pro_upgrade_button, 2, 0, 1, 2)

        # Set stretch to make rows/columns resize equally
        group_layout.setRowStretch(0, 1)
        group_layout.setRowStretch(1, 1)
        group_layout.setRowStretch(2, 1)
        group_layout.setColumnStretch(0, 1)
        group_layout.setColumnStretch(1, 1)

        main_layout.addWidget(group_box)
        settings_window.exec()

    def change_data_location(self):
        global active_dir, store_dir

        # Open a directory dialog for the user to select a new directory
        new_path = QFileDialog.getExistingDirectory(
            self, "Select a New Path for Active and Store Folders"
        )

        if not new_path:
            print("No directory selected. Operation canceled.")
            return

        try:
            # Check if the selected path is valid
            if not os.path.exists(new_path):
                print(f"The selected path does not exist: {new_path}")
                return

            # Create new Active and Store directories in the chosen path
            new_active_dir = os.path.join(new_path, 'Active')
            new_store_dir = os.path.join(new_path, 'Store')

            # Move the existing Active and Store directories to the new path
            if os.path.exists(active_dir):
                shutil.move(active_dir, new_active_dir)
                print(f"Moved Active folder to {new_active_dir}")
            else:
                print(f"Active folder does not exist at {active_dir}")

            if os.path.exists(store_dir):
                shutil.move(store_dir, new_store_dir)
                print(f"Moved Store folder to {new_store_dir}")
            else:
                print(f"Store folder does not exist at {store_dir}")

            # Update the condition.json file with the new path
            new_condition_data = {"path": new_path}
            with open(condition_path, 'w') as f:
                json.dump(new_condition_data, f)
            print(f"Updated condition.json with the new path: {new_path}")

            # Update the global active_dir and store_dir variables to point to the new locations
            active_dir = new_active_dir
            store_dir = new_store_dir
            print(f"Global active_dir updated to: {active_dir}")
            print(f"Global store_dir updated to: {store_dir}")

            # Refresh the UI and reload the scripts
            self.SCRIPT_DIR = active_dir
            self.scripts = self.list_scripts()
            self.update_script_list()  # Refresh the UI to reflect the updated scripts

            # Show a success message box
            QMessageBox.information(self, "Change Profile Location", "Profile location changed successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def get_latest_version(self):
        """
        Checks GitHub for the latest KeyTik version.
        Returns the latest version string if successful, else None.
        """
        try:
            response = requests.get("https://api.github.com/repos/Fajar-RahmadJaya/KeyTik/releases/latest", timeout=5)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get("tag_name")
                return latest_version
        except Exception as e:
            print(f"Error checking for update: {e}")
        return None

    def show_update_messagebox(self, latest_version):
        """
        Shows a QMessageBox indicating update status.
        """
        if not latest_version:
            QMessageBox.critical(self, "Error", "Failed to check for updates. Please try again later.")
            return

        if current_version == latest_version:
            QMessageBox.information(self, "Check For Update", "You are using the latest version of KeyTik.")
        else:
            QMessageBox.information(self, "Check For Update", f"New update available: KeyTik {latest_version}")

    def check_for_update(self, show_no_update_message=False):
        """
        Checks for update and shows a message box.
        If show_no_update_message is True, always show a message.
        """
        latest_version = self.get_latest_version()
        if latest_version:
            if current_version == latest_version:
                if show_no_update_message:
                    QMessageBox.information(self, "Check For Update", "You are using the latest version of KeyTik.")
            else:
                QMessageBox.information(self, "Check For Update", f"New update available: KeyTik {latest_version}")
        else:
            QMessageBox.critical(self, "Error", "Failed to check for updates. Please try again later.")

    def change_theme_dialog(self):
        # Show a dialog to pick theme
        options = ["Light", "Dark", "System"]
        current_theme = self.get_saved_theme()
        if current_theme == "dark":
            current_index = 1
        elif current_theme == "light":
            current_index = 0
        else:
            current_index = 2  # system or empty
        theme, ok = QInputDialog.getItem(self, "Change Theme", "Select theme:", options, current_index, False)
        if ok:
            # Save the theme to theme_path
            self.save_theme(theme.lower())
            QMessageBox.information(self, "Theme Changed", "Theme will be applied after restarting the app.")

    def get_saved_theme(self):
        # Read theme from theme_path, default to system (empty or missing)
        try:
            if os.path.exists(theme_path):
                with open(theme_path, 'r') as f:
                    theme = f.read().strip().lower()
                if theme in ("dark", "light"):
                    return theme
            return "system"
        except Exception:
            return "system"

    def save_theme(self, theme):
        # Save theme to theme_path, empty for system
        try:
            with open(theme_path, 'w') as f:
                if theme == "system":
                    f.write("")
                else:
                    f.write(theme)
        except Exception as e:
            print(f"Failed to save theme: {e}")