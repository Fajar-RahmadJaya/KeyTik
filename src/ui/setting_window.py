import os
import shutil
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QGroupBox, QPushButton, QMessageBox, QFileDialog
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import webbrowser
import requests
import json
from src.utility.constant import (current_version, icon_path, condition_path)
from src.utility.utils import (active_dir)

class setting_window:
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
        on_boarding_button = QPushButton("On Boarding")
        on_boarding_button.setFixedHeight(40)
        on_boarding_button.setFixedWidth(180)
        on_boarding_button.clicked.connect(self.show_welcome_window)
        group_layout.addWidget(on_boarding_button, 1, 0, 1, 1)

        # Credit button (disabled)
        credit_button = QPushButton("Credit")
        credit_button.setFixedHeight(40)
        credit_button.setFixedWidth(180)
        credit_button.setEnabled(False)
        group_layout.addWidget(credit_button, 1, 1, 1, 1)

        # Sponsor Me button
        sponsor_button = QPushButton("Sponsor Me")
        sponsor_button.setFixedHeight(40)
        sponsor_button.setFixedWidth(370)
        sponsor_button.clicked.connect(lambda: webbrowser.open("https://github.com/sponsors/Fajar-RahmadJaya"))
        group_layout.addWidget(sponsor_button, 2, 0, 1, 2)

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

    def check_for_update(self, show_no_update_message=False):
        try:
            # Make a GET request to your website to get the latest version
            response = requests.get("https://keytik.com/pro-version.txt")
            if response.status_code == 200:
                # Get the version number from the response text and strip whitespace
                latest_version = response.text.strip()
                if not latest_version.startswith('v'):
                    latest_version = 'v' + latest_version

                if current_version == latest_version:
                    # Only show up-to-date message if explicitly requested (button click)
                    if show_no_update_message:
                        QMessageBox.information(self, "Check For Update", "You are using the latest version of KeyTik Pro.")
                else:
                    # If update is available, show message with option to update
                    reply = QMessageBox.question(
                        self, "Update Available",
                        f"New update available: KeyTik Pro {latest_version}\n\nWould you like to go to the update page?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        webbrowser.open("https://gumroad.com/library")
            else:
                QMessageBox.critical(self, "Error", "Failed to check for updates. Please try again later.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while checking for updates: {str(e)}")