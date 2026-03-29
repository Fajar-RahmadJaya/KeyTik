"Setting UI code"

import os
import webbrowser

from PySide6.QtWidgets import ( # pylint: disable=E0611
    QDialog, QVBoxLayout, QGridLayout, QGroupBox, QPushButton,
    QHBoxLayout, QCheckBox, QInputDialog, QMessageBox
)
from PySide6.QtGui import QIcon # pylint: disable=E0611
from PySide6.QtCore import Qt # pylint: disable=E0611

from utility import constant
from utility import utils

from setting.setting_core import SettingCore

from core.main_logic import MainLogic


class SettingUI(SettingCore):
    "Setting UI"
    def __init__(self):
        super().__init__()
        self.main_logic = MainLogic()

    def open_settings_window(self):
        "Setting window"
        settings_window = QDialog(self)
        settings_window.setWindowTitle("Settings")
        settings_window.setFixedSize(400, 250)
        settings_window.setWindowIcon(QIcon(constant.icon_path))
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
        readme_button.clicked.connect(self.main_logic.show_announcement_window)
        group_layout.addWidget(readme_button, 2, 1, 1, 1)

        group_layout.setRowStretch(0, 1)
        group_layout.setRowStretch(1, 1)
        group_layout.setRowStretch(2, 1)
        group_layout.setColumnStretch(0, 1)
        group_layout.setColumnStretch(1, 1)

        main_layout.addWidget(group_box)
        settings_window.exec()

    def show_installation_dialog(self):
        "Setting to check, install, uninstall AutoHotkey and Interception driver installation"
        dialog = QDialog(self)
        dialog.setWindowTitle("Installation Manager")
        dialog.setWindowIcon(QIcon(constant.icon_path))
        dialog.setFixedSize(380, 180)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        install_group = QGroupBox()
        install_group_layout = QHBoxLayout(install_group)
        install_group_layout.setContentsMargins(10, 10, 10, 10)

        ahk_vbox = QVBoxLayout()
        ahk_checkbox = QCheckBox("AutoHotkey", dialog)
        ahk_installed = os.path.exists(utils.ahkv2_dir)
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
        driver_installed = os.path.exists(constant.DRIVER_PATH)
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

        ahk_button.clicked.connect(lambda: self.ahk_action(
            ahk_installed, dialog))
        driver_button.clicked.connect(lambda: self.driver_action(
            driver_installed, dialog))

        dialog.exec()

    def change_theme_dialog(self):
        "Setting to change program theme"
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
            QMessageBox.information(self,
                                    "Theme Changed", 
                                    "Theme will be applied after restarting the app.") # noqa
