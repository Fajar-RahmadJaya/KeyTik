import os
import shutil
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QGroupBox, QPushButton,
    QMessageBox, QFileDialog, QInputDialog, QHBoxLayout, QCheckBox
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
import webbrowser
import json
import subprocess
import ctypes
from utility.constant import (icon_path,
                              condition_path, theme_path,
                              ahk_path, driver_path,
                              interception_install_path,
                              interception_uninstall_path)
from utility.utils import (active_dir, store_dir) # noqa


class Setting:
    def open_settings_window(self):
        settings_window = QDialog(self)
        settings_window.setWindowTitle("Settings")
        # settings_window.setGeometry(400, 225, 400, 300)
        settings_window.setFixedSize(400, 250)
        settings_window.setWindowIcon(QIcon(icon_path))
        settings_window.setModal(True)
        settings_window.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            getattr(self, "is_on_top", False))

        main_layout = QVBoxLayout(settings_window)
        main_layout.setContentsMargins(10, 10, 10, 10)

        group_box = QGroupBox()
        group_layout = QGridLayout(group_box)
        group_layout.setHorizontalSpacing(20)
        group_layout.setContentsMargins(10, 10, 10, 10)

        theme_button = QPushButton("Change Theme")
        theme_button.setFixedHeight(40)
        theme_button.clicked.connect(self.change_theme_dialog)
        group_layout.addWidget(theme_button, 0, 0, 1, 1)

        change_path_button = QPushButton("Change Profile Location")
        change_path_button.setFixedHeight(40)
        change_path_button.clicked.connect(self.change_data_location)
        group_layout.addWidget(change_path_button, 0, 1, 1, 1)

        installation_button = QPushButton("Check Installation")
        installation_button.setFixedHeight(40)
        installation_button.clicked.connect(self.show_installation_dialog)
        group_layout.addWidget(installation_button, 1, 0, 1, 1)

        check_update_button = QPushButton("Check For Update")
        check_update_button.setFixedHeight(40)
        check_update_button.clicked.connect(
            self.check_update_and_show_messagebox)
        group_layout.addWidget(check_update_button, 1, 1, 1, 1)

        pro_upgrade_button = QPushButton("Get KeyTik Pro")
        pro_upgrade_button.setFixedHeight(40)
        pro_upgrade_button.clicked.connect(
            lambda: webbrowser.open(
                "https://fajarrahmadjaya.gumroad.com/l/keytik-pro"))
        group_layout.addWidget(pro_upgrade_button, 2, 0, 1, 1)

        readme_button = QPushButton("Announcement")
        readme_button.setFixedHeight(40)
        readme_button.clicked.connect(self.show_welcome_window)
        group_layout.addWidget(readme_button, 2, 1, 1, 1)

        group_layout.setRowStretch(0, 1)
        group_layout.setRowStretch(1, 1)
        group_layout.setRowStretch(2, 1)
        group_layout.setColumnStretch(0, 1)
        group_layout.setColumnStretch(1, 1)

        main_layout.addWidget(group_box)
        settings_window.exec()

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
                shutil.move(active_dir, new_active_dir)
                print(f"Moved Active folder to {new_active_dir}")
            else:
                print(f"Active folder does not exist at {active_dir}")

            if os.path.exists(store_dir):
                shutil.move(store_dir, new_store_dir)
                print(f"Moved Store folder to {new_store_dir}")
            else:
                print(f"Store folder does not exist at {store_dir}")

            new_condition_data = {"path": new_path}
            with open(condition_path, 'w') as f:
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

    def update_messagebox(self, latest_version, show_no_update_message=False): # noqa
        if latest_version:
            reply = QMessageBox.question(
                self, "Update Available",
                f"New update available: KeyTik {latest_version}\n\nWould you like to go to the update page?", # noqa
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No # noqa
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("https://github.com/Fajar-RahmadJaya/KeyTik/releases") # noqa
        else:
            if show_no_update_message:
                QMessageBox.information(
                    self, "Check For Update",
                    "You are using the latest version of KeyTik.")

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
            if os.path.exists(theme_path):
                with open(theme_path, 'r') as f:
                    theme = f.read().strip().lower()
                if theme in ("dark", "light"):
                    return theme
            return "system"
        except Exception:
            return "system"

    def save_theme(self, theme):
        try:
            with open(theme_path, 'w') as f:
                if theme == "system":
                    f.write("")
                else:
                    f.write(theme)
        except Exception as e:
            print(f"Failed to save theme: {e}")

    def show_installation_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Installation Manager")
        dialog.setWindowIcon(QIcon(icon_path))
        # dialog.setGeometry(414, 248, 380, 180)
        dialog.setFixedSize(380, 180)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        install_group = QGroupBox()
        install_group_layout = QHBoxLayout(install_group)
        install_group_layout.setContentsMargins(10, 10, 10, 10)

        ahk_vbox = QVBoxLayout()
        ahk_checkbox = QCheckBox("AutoHotkey", dialog)
        ahk_installed = os.path.exists(ahk_path)
        ahk_checkbox.setChecked(ahk_installed)
        ahk_checkbox.setEnabled(False)
        ahk_button = QPushButton(dialog)
        ahk_button.setText(
            "Uninstall AutoHotkey"
            if ahk_installed
            else "Install AutoHotkey")
        ahk_vbox.addWidget(
            ahk_checkbox, alignment=Qt.AlignmentFlag.AlignHCenter)
        ahk_vbox.addWidget(ahk_button)

        driver_vbox = QVBoxLayout()
        driver_checkbox = QCheckBox("Interception Driver", dialog)
        driver_installed = os.path.exists(driver_path)
        driver_checkbox.setChecked(driver_installed)
        driver_checkbox.setEnabled(False)
        driver_button = QPushButton(dialog)
        driver_button.setText(
            "Uninstall Interception Driver"
            if driver_installed
            else "Install Interception Driver")
        driver_vbox.addWidget(
            driver_checkbox, alignment=Qt.AlignmentFlag.AlignHCenter)
        driver_vbox.addWidget(driver_button)

        install_group_layout.addLayout(ahk_vbox)
        install_group_layout.addLayout(driver_vbox)

        layout.addWidget(install_group)

        def ahk_action():
            if ahk_installed:
                uninstall_cmd = f'"{ahk_path}" "{os.path.join(os.path.dirname(ahk_path), "ui-uninstall.ahk")}"' # noqa
                try:
                    subprocess.Popen(uninstall_cmd, shell=True)
                except Exception as e:
                    QMessageBox.critical(dialog, "Error", f"Failed to start uninstall: {e}") # noqa
            else:
                webbrowser.open("https://www.autohotkey.com")

        def driver_action():
            try:
                if driver_installed:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas",
                        interception_uninstall_path, None, None, 1
                    )
                else:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", interception_install_path, None, None, 1
                    )
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Failed to run driver installer/uninstaller: {e}") # noqa

        ahk_button.clicked.connect(ahk_action)
        driver_button.clicked.connect(driver_action)

        dialog.exec()
