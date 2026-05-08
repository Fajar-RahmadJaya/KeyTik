"Setting UI code"

import os
import webbrowser
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QVBoxLayout, QGroupBox, QPushButton,
    QHBoxLayout, QCheckBox, QMessageBox, QScrollArea,
    QFrame, QWidget, QLabel, QSizePolicy, QComboBox,
    QStyleFactory)
from PySide6.QtGui import QIcon, QFont  # pylint: disable=E0611
from PySide6.QtCore import Qt  # pylint: disable=E0611

from utility import constant
from utility import utils
from utility import diff
from utility import style
from setting.setting_core import SettingCore
from setting.announcement import Announcement


class SettingUI():
    "Setting UI"
    def __init__(self):
        # Composition
        self.setting_core = SettingCore()

    # ------------------------------ Template ------------------------------
    def setting_card(self, heading="", subheading=""):
        "Setting card template"
        card_frame = QFrame()
        card_frame.setFrameShape(QFrame.NoFrame)
        card_frame.setObjectName("settingCardFrame")
        card_frame.setStyleSheet(style.setting_card_style())

        card_layout = QHBoxLayout(card_frame)
        card_layout.setContentsMargins(16, 16, 16, 16)

        theme_label = QLabel(
            f"<div style='{style.HEADING_STYLE}'> {heading} </div>"
            f"<div style=' {style.SUBHEADING_STYLE}'> {subheading} </div>"
        )
        card_layout.addWidget(theme_label)

        return card_layout, card_frame

    def setting_combobox(self):
        "Setting combobox template"
        setting_combobox = QComboBox()
        setting_combobox.setFixedWidth(164)
        setting_combobox.setEditable(True)
        setting_combobox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        setting_combobox.lineEdit().setReadOnly(True)
        setting_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        return setting_combobox

    def setting_button(self):
        "Setting button template"
        setting_button = QPushButton()
        setting_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        setting_button.setFixedWidth(164)

        return setting_button

    def setting_header_label(self):
        "Setting header label template"
        setting_header_font = QFont()
        setting_header_font.setBold(True)
        setting_header_font.setPixelSize(13)

        setting_header_label = QLabel()
        setting_header_label.setFont(setting_header_font)
        setting_header_label.setContentsMargins(0, 0, 0, 4)

        return setting_header_label

    # ------------------------------ UI ------------------------------
    def setting_window(self, parent):
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
        content_layout.setSpacing(28)
        content_layout.setContentsMargins(8, 8, 8, 8)

        # Pro Version
        content_layout.addWidget(self.pro_version())

        # Appearance
        content_layout.addWidget(self.appearance(settings_window))

        # General
        content_layout.addWidget(self.general(settings_window))

        # Advanced
        content_layout.addWidget(self.advanced(settings_window))

        setting_layout.addWidget(scroll_area)
        settings_window.exec()

    def pro_version(self):
        "Pro version setting"
        pro_version_widget = QWidget()
        pro_version_layout = QVBoxLayout(pro_version_widget)
        pro_version_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        pro_version_label = self.setting_header_label()
        pro_version_label.setText("Pro Version")
        pro_version_layout.addWidget(pro_version_label)

        # Upgrade to Pro Version
        pro_upgrade_button = self.setting_button()
        pro_upgrade_button.setText("Get KeyTik Pro")
        pro_upgrade_button.clicked.connect(
            lambda: webbrowser.open(
                "https://fajarrahmadjaya.gumroad.com/l/keytik-pro"))

        pro_upgrade_layout, pro_upgrade_frame = self.setting_card(heading="Get KeyTik Pro",
                                                subheading="Support the developer")
        pro_upgrade_layout.addWidget(pro_upgrade_button)
        pro_version_layout.addWidget(pro_upgrade_frame)

        return pro_version_widget

    def appearance(self, settings_window):
        "Appearance setting"
        appearance_widget = QWidget()
        appearance_layout = QVBoxLayout(appearance_widget)
        appearance_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        appearance_label = self.setting_header_label()
        appearance_label.setText("Appearance")
        appearance_layout.addWidget(appearance_label)

        # Style
        style_combobox = self.setting_combobox()
        style_combobox.addItem("Default")
        style_combobox.addItems(QStyleFactory.keys())
        current_style = utils.get_config().style
        style_combobox.setCurrentText(current_style if current_style
                                        else "Default")
        style_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_style(style=style_combobox.currentText(),
                                                    parent=settings_window))

        style_layout, style_frame = self.setting_card(heading="Style",
                                            subheading="Change overall appearance style")
        style_layout.addWidget(style_combobox)
        appearance_layout.addWidget(style_frame)

        # Theme
        theme_combobox = self.setting_combobox()
        theme_combobox.addItems(["Light", "Dark", "System"])
        theme_combobox.setCurrentText(utils.get_config().theme.capitalize())
        theme_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_theme(theme=theme_combobox.currentText(),
                                                 parent=settings_window))

        theme_layout, theme_frame = self.setting_card(heading="Theme",
                                         subheading="Change KeyTik theme")
        theme_layout.addWidget(theme_combobox)
        appearance_layout.addWidget(theme_frame)

        return appearance_widget

    def general(self, settings_window):
        "General setting"
        general_widget = QWidget()
        general_layout = QVBoxLayout(general_widget)
        general_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        general_label = self.setting_header_label()
        general_label.setText("General")
        general_layout.addWidget(general_label)

        # Profile Location
        profile_location_button = self.setting_button()
        profile_location_button.setText("Change Location")
        profile_location_button.clicked.connect(
            lambda: self.setting_core.change_data_location(settings_window))

        profile_location_layout, profile_location_frame = self.setting_card(
            heading="Profile Location",
            subheading=utils.get_config().profile_path)
        profile_location_layout.addWidget(profile_location_button)
        general_layout.addWidget(profile_location_frame)

        # Announcement
        announcement = Announcement()  # Composition
        announcement_button = self.setting_button()
        announcement_button.setText("Announcement")
        announcement_button.clicked.connect(
            lambda: announcement.show_announcement_window(settings_window))

        announcement_layout, announcement_frame = self.setting_card(heading="Announcement",
                                            subheading="Show announcement")
        announcement_layout.addWidget(announcement_button)
        general_layout.addWidget(announcement_frame)

        return general_widget

    def advanced(self, settings_window):
        "Advanced setting"
        advanced_widget = QWidget()
        advanced_layout = QVBoxLayout(advanced_widget)
        advanced_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        advanced_label = self.setting_header_label()
        advanced_label.setText("Advanced")
        advanced_layout.addWidget(advanced_label)

        # Installation
        installation_button = self.setting_button()
        installation_button.setText("Check Installation")
        installation_button.clicked.connect(
            lambda: self.show_installation_dialog(settings_window))

        installation_layout, installation_frame = self.setting_card(heading="Installtion",
                                                subheading="Check installation")
        installation_layout.addWidget(installation_button)
        advanced_layout.addWidget(installation_frame)

        # Check for Update
        check_update_button = self.setting_button()
        check_update_button.setText("Check For Update")
        check_update_button.clicked.connect(
            lambda: self.update_messagebox(show_no_update_message=True))

        check_update_layout, check_update_frame = self.setting_card(heading="Check for update",
                                                subheading="Check for update")
        check_update_layout.addWidget(check_update_button)
        advanced_layout.addWidget(check_update_frame)

        return advanced_widget

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
