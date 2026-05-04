"Setting UI code"

import os
import webbrowser
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QVBoxLayout, QGroupBox, QPushButton,
    QHBoxLayout, QCheckBox, QInputDialog, QMessageBox, QScrollArea,
    QFrame, QWidget, QLabel, QSizePolicy)
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from PySide6.QtCore import Qt  # pylint: disable=E0611

from utility import constant
from utility import utils
from utility import diff
from setting.setting_core import SettingCore
from setting.announcement import Announcement


class SettingUI():
    "Setting UI"
    def __init__(self):
        # Composition
        self.setting_core = SettingCore()

    def open_settings_window(self, parent):
        "Setting window"
        settings_window = QDialog(parent)
        settings_window.setWindowTitle("Settings")
        geometry = utils.get_geometry(parent, 600, 400)
        settings_window.setGeometry(geometry)
        settings_window.setWindowIcon(QIcon(constant.icon_path))

        setting_layout = QVBoxLayout(settings_window)
        setting_layout.setContentsMargins(12, 12, 12, 12)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("settingScroll")
        scroll_area.setStyleSheet("#settingScroll {background-color: transparent;}")
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("#contentWidget {background-color: transparent;}")
        scroll_area.setWidget(content_widget)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(8, 8, 8, 8)

        # Theme
        content_layout.addWidget(self.appearance(settings_window))

        # Change profile location
        content_layout.addWidget(self.change_profile(settings_window))

        # Check installation
        content_layout.addWidget(self.installation(settings_window))

        # Check for update
        content_layout.addWidget(self.check_update())

        # Get KeyTik Pro
        content_layout.addWidget(self.keytik_pro())

        # Show announcement
        content_layout.addWidget(self.announcement(settings_window))

        setting_layout.addWidget(scroll_area)
        settings_window.exec()

    def setting_card(self, heading="", subheading=""):
        "Card for each setting"
        card_frame = QFrame()
        card_frame.setFrameShape(QFrame.NoFrame)
        card_frame.setObjectName("settingCardFrame")

        if utils.theme == "dark":
            style_sheet = """
            QFrame#settingCardFrame {
                background: rgba(255, 255, 255, 0.052);
                border-radius: 4;
            }
            """
        else:
            style_sheet = """
            QFrame#settingCardFrame {
                background: rgba(255, 255, 255, 0.60);
                border-radius: 4;
            }
            """

        card_frame.setStyleSheet(style_sheet)

        card_layout = QHBoxLayout(card_frame)
        card_layout.setContentsMargins(16, 16, 16, 16)

        theme_label = QLabel(
            f"<div style='font-size:13px; margin-bottom:2px'> {heading} </div>"
            f"<div style='font-size:11px; color: rgba(255,255,255,0.8); '> {subheading} </div>"
        )
        card_layout.addWidget(theme_label)

        return card_layout, card_frame

    def appearance(self, settings_window):
        "Appearance widget"
        theme_button = QPushButton("Change Theme")
        theme_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        theme_button.setFixedWidth(164)
        theme_button.clicked.connect(lambda: self.change_theme_dialog(settings_window))

        theme_layout, theme_frame = self.setting_card(heading="Appearance",
                                         subheading="Change KeyTik theme")
        theme_layout.addWidget(theme_button)

        return theme_frame

    def change_profile(self, settings_window):
        "Change profile location widget"
        change_path_button = QPushButton("Change Profile Location")
        change_path_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        change_path_button.setFixedWidth(164)
        change_path_button.clicked.connect(
            lambda: self.setting_core.change_data_location(settings_window))

        change_path_layout, change_path_frame = self.setting_card(heading="Profile Location",
                                               subheading="Change where profile stored")
        change_path_layout.addWidget(change_path_button)

        return change_path_frame

    def installation(self, settings_window):
        "Check installation widget"
        installation_button = QPushButton("Check Installation")
        installation_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        installation_button.setFixedWidth(164)
        installation_button.clicked.connect(
            lambda: self.show_installation_dialog(settings_window))

        installation_layout, installation_frame = self.setting_card(heading="Installtion",
                                                subheading="Check installation")
        installation_layout.addWidget(installation_button)

        return installation_frame

    def check_update(self):
        "Check update widget"
        check_update_button = QPushButton("Check For Update")
        check_update_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        check_update_button.setFixedWidth(164)
        check_update_button.clicked.connect(
            lambda: self.update_messagebox(show_no_update_message=True))

        check_update_layout, check_update_frame = self.setting_card(heading="Check for update",
                                                subheading="Check for update")
        check_update_layout.addWidget(check_update_button)

        return check_update_frame

    def keytik_pro(self):
        "Get KeyTik pro widget"
        pro_upgrade_button = QPushButton("Get KeyTik Pro")
        pro_upgrade_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        pro_upgrade_button.setFixedWidth(164)
        pro_upgrade_button.clicked.connect(
            lambda: webbrowser.open(
                "https://fajarrahmadjaya.gumroad.com/l/keytik-pro"))

        pro_upgrade_layout, pro_upgrade_frame = self.setting_card(heading="Get KeyTik Pro",
                                               subheading="Support the developer")
        pro_upgrade_layout.addWidget(pro_upgrade_button)

        return pro_upgrade_frame

    def announcement(self, settings_window):
        "Announcement widget"
        announcement = Announcement()  # Composition

        readme_button = QPushButton("Announcement")
        readme_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        readme_button.setFixedWidth(164)
        readme_button.clicked.connect(
            lambda: announcement.show_announcement_window(settings_window))

        readme_layout, readme_frame = self.setting_card(heading="Announcement",
                                          subheading="Show announcement")
        readme_layout.addWidget(readme_button)

        return readme_frame

    def show_installation_dialog(self, parent):
        "Setting to check, install, uninstall AutoHotkey and Interception driver installation"
        dialog = QDialog(parent)
        dialog.setWindowTitle("Installation Manager")
        dialog.setWindowIcon(QIcon(constant.icon_path))
        geometry = utils.get_geometry(parent, 380, 180)
        dialog.setGeometry(geometry)
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

        ahk_button.clicked.connect(lambda: self.setting_core.ahk_action(
            ahk_installed))
        driver_button.clicked.connect(lambda: self.setting_core.driver_action(
            driver_installed))

        dialog.exec()

    def change_theme_dialog(self, parent):
        "Setting to change program theme"
        options = ["Light", "Dark", "System"]
        current_theme = self.setting_core.read_theme()
        if current_theme == "dark":
            current_index = 1
        elif current_theme == "light":
            current_index = 0
        else:
            current_index = 2
        theme, ok = QInputDialog.getItem(
            parent, "Change Theme", "Select theme:",
            options, current_index, False)
        if ok:
            self.setting_core.save_theme(theme.lower())
            QMessageBox.information(None,
                                    "Theme Changed", 
                                    "Theme will be applied after restarting the app.") 

    def update_messagebox(self, show_no_update_message=False):
        "Message when there is update avalible"
        latest_version = self.setting_core.check_for_update()
        if latest_version:
            reply = QMessageBox.question(
                None, "Update Available",
                (
                f"New update available: {diff.PROGRAM_NAME} {latest_version}\n\n"
                "Would you like to go to the update page?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open(diff.RELEASE_LINK)
        else:
            if show_no_update_message:
                QMessageBox.information(
                    None, "Check For Update",
                    "You are using the latest version of KeyTik.")
