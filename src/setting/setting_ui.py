"Setting UI code"

import os
import webbrowser
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QDialog, QVBoxLayout, QPushButton,
    QHBoxLayout, QMessageBox, QScrollArea,
    QFrame, QWidget, QLabel, QSizePolicy, QComboBox,
    QStyleFactory)
from PySide6.QtGui import QIcon, QFont  # pylint: disable=E0611
import qt_themes

from utility import constant
from utility import utils
from utility import diff
from utility import style
from setting.setting_core import SettingCore
from setting.announcement import Announcement

class SettingCombobox(QComboBox):  # pylint: disable=R0903
    "Ignore Wheel Event"
    def wheelEvent(self, event):  # pylint: disable=C0103
        "Override wheelEvent"
        event.ignore()

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
        card_frame.setObjectName("setting")
        card_frame.setStyleSheet(style.card("setting"))

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
        setting_combobox = SettingCombobox()
        setting_combobox.setFixedWidth(164)
        setting_combobox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

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

    # ------------------------------ Window ------------------------------
    def setting_window(self, parent):
        "Setting window"
        settings_window = QDialog(parent)
        settings_window.setWindowTitle("Settings")
        geometry = style.get_geometry(parent, 600, 400)
        settings_window.setGeometry(geometry)
        settings_window.setWindowIcon(QIcon(constant.icon_path))
        style.apply_mica(settings_window)

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
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(8, 8, 8, 8)

        # Pro Version
        if diff.PROGRAM_NAME != "KeyTik Pro":
            content_layout.addWidget(self.pro_version())

        # Appearance
        content_layout.addWidget(self.appearance(settings_window))

        # General
        content_layout.addWidget(self.general(settings_window))

        # Advanced
        content_layout.addWidget(self.installation())

        setting_layout.addWidget(scroll_area)
        settings_window.exec()

    # ------------------------------ Pro Version ------------------------------
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
        pro_upgrade_button.setStyleSheet(style.button_highlight(pro_upgrade_button))

        pro_upgrade_layout, pro_upgrade_frame = self.setting_card(heading="KeyTik Pro",
                                                subheading="Pro version available at $20")
        pro_upgrade_layout.addWidget(pro_upgrade_button)
        pro_version_layout.addWidget(pro_upgrade_frame)

        return pro_version_widget

    # ------------------------------ Appearance ------------------------------
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
        appearance_layout.addWidget(self.style(settings_window))

        # Theme
        appearance_layout.addWidget(self.theme(settings_window))

        # Mica Effect
        if style.mica_supported:
            appearance_layout.addWidget(self.mica_effect(settings_window))

        return appearance_widget

    def style(self, settings_window):
        "Style Widget"
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
                                            subheading="Change appearance style")
        style_layout.addWidget(style_combobox)

        return style_frame

    def theme(self, settings_window):
        "Theme Widget"
        theme_combobox = self.setting_combobox()

        # Default theme
        theme_combobox.addItem("Light", "light")
        theme_combobox.addItem("Dark", "dark")
        theme_combobox.addItem("System", "system")

        # qt-themes theme
        qt_themes_dict = qt_themes.get_themes()
        for theme, _ in qt_themes_dict.items():
            if not theme.startswith("catppuccin"):
                theme_combobox.addItem(theme.replace('_', ' ').title(), theme)

        # conf theme
        conf_list = self.setting_core.catppuccin_conf()
        for file in conf_list:
            catppuccin_theme = file.replace('.conf', '')
            theme_combobox.addItem(catppuccin_theme.replace('-', ' ').title(), catppuccin_theme)

        current_text = utils.get_config().theme.replace('_', ' ').replace('-', ' ').title()
        theme_combobox.setCurrentText(current_text)
        theme_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_theme(theme=theme_combobox.currentData(),
                                                    parent=settings_window))

        theme_layout, theme_frame = self.setting_card(heading="Theme",
                                            subheading="Change appearance theme")
        theme_layout.addWidget(theme_combobox)

        return theme_frame

    def mica_effect(self, settings_window):
        "Mica Effect Widget"
        mica_combobox = self.setting_combobox()
        mica_combobox.addItems(["Default", "Alt", "Disable"])
        mica_combobox.setCurrentText(utils.get_config().mica_effect.capitalize())
        mica_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_mica_effect(
                mica_effect=mica_combobox.currentText(),
                parent=settings_window))

        mica_layout, mica_frame = self.setting_card(heading="Mica Effect",
                                            subheading="Enable/Disable Mica Effect")
        mica_layout.addWidget(mica_combobox)

        return mica_frame

    # ------------------------------ General ------------------------------
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
        general_layout.addWidget(self.profile_location(settings_window=()))

        # Announcement
        general_layout.addWidget(self.announcement(settings_window))

        return general_widget

    def profile_location(self, settings_window):
        "Profile Location Widget"
        profile_location_button = self.setting_button()
        profile_location_button.setText("Change Location")
        profile_location_button.clicked.connect(
            lambda: self.setting_core.change_data_location(settings_window))

        profile_location_layout, profile_location_frame = self.setting_card(
            heading="Profile Location",
            subheading=utils.get_config().profile_path)
        profile_location_layout.addWidget(profile_location_button)

        return profile_location_frame

    def announcement(self, settings_window):
        "Announcement Widget"
        announcement = Announcement()  # Composition
        announcement_button = self.setting_button()
        announcement_button.setText("Announcement")
        announcement_button.clicked.connect(
            lambda: announcement.show_announcement_window(settings_window))

        announcement_layout, announcement_frame = self.setting_card(heading="Announcement",
                                            subheading="Show announcement")
        announcement_layout.addWidget(announcement_button)

        return announcement_frame

    # ------------------------------ Installation ------------------------------
    def installation(self):
        "Advanced setting"
        installation_widget = QWidget()
        installation_layout = QVBoxLayout(installation_widget)
        installation_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        installaation_label = self.setting_header_label()
        installaation_label.setText("Installation")
        installation_layout.addWidget(installaation_label)

        # AutoHotkey Installation
        installation_layout.addWidget(self.ahk_installation())

        # Interception Driver Installation
        installation_layout.addWidget(self.interception_installation())

        # Check for Update
        installation_layout.addWidget(self.check_update())

        return installation_widget

    def ahk_installation(self):
        "AutoHotkey Installation Widget"
        ahk_installed = os.path.exists(utils.ahkv2_dir)

        ahk_button = self.setting_button()
        ahk_button.setDisabled(bool(ahk_installed))
        ahk_button.setText(
            "Uninstall AutoHotkey"
            if ahk_installed
            else "Install AutoHotkey")
        ahk_button.clicked.connect(
            lambda: self.setting_core.ahk_action(ahk_installed))

        ahk_layout, ahk_frame = self.setting_card(
            heading="AutoHotkey Installation",
            subheading=("AutoHotkey is installed" if ahk_installed
                        else "AutoHotkey not installed"))
        ahk_layout.addWidget(ahk_button)

        return ahk_frame

    def interception_installation(self):
        "Interception Driver Installation"
        interception_installed = os.path.exists(constant.DRIVER_PATH)

        interception_button = self.setting_button()
        interception_button.setDisabled(bool(interception_installed))
        interception_button.setText(
                                "Uninstall Interception Driver"
                                if interception_installed
                                else "Install Interception Driver")
        interception_button.clicked.connect(
            lambda: self.setting_core.driver_action(interception_installed))

        interception_layout, interception_frame = self.setting_card(
            heading="Interception Driver Installation",
            subheading=("Interception Driver is Installed" if interception_installed
                        else "Interception Driver not Installed"))
        interception_layout.addWidget(interception_button)

        return interception_frame

    def check_update(self):
        "Check for Update Widget"
        check_update_button = self.setting_button()
        check_update_button.setText("Check For Update")
        check_update_button.clicked.connect(
            lambda: self.update_messagebox(show_no_update_message=True))

        check_update_layout, check_update_frame = self.setting_card(heading="Check for update",
                                                subheading="Check for update")
        check_update_layout.addWidget(check_update_button)

        return check_update_frame

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
