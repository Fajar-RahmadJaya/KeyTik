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

"""Setting UI code."""

import json
import os
import webbrowser

import qt_themes
from catppuccin import PALETTE as catppuccin_palette
from plwidgets.pl_checkbox import PlCheckBox
from PySide6.QtCore import QSize, Qt  # pylint: disable=E0611
from PySide6.QtGui import (  # pylint: disable=E0611
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPalette,
    QPixmap,
)
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QStyleFactory,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from keytik.setting.announcement import Announcement
from keytik.setting.setting_core import SettingCore
from keytik.utility import constant, diff, icons
from keytik.utility.style import Palette, Styling
from keytik.utility.utils import Config, Data, Utility


class SettingCombobox(QComboBox):  # pylint: disable=R0903
    """Ignore Wheel Event."""

    def wheelEvent(self, event):  # pylint: disable=C0103
        """Override wheelEvent."""
        event.ignore()


class SettingTemplate:
    """Widget template to use across setting UI."""

    def setting_card(self, icon_code=None, heading=None, subheading=None):
        """Setting card template."""
        card_frame = QFrame()
        card_frame.setFrameShape(QFrame.NoFrame)
        card_frame.setObjectName("setting")
        card_frame.setStyleSheet(Styling().card("setting"))

        card_layout = QHBoxLayout()
        card_frame.setLayout(card_layout)

        if icon_code:
            card_layout.setContentsMargins(20, 16, 16, 16)
            card_layout.setSpacing(20)

            icon = self.adaptive_icon(icon_code, 16)
            icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            card_layout.addWidget(icon)
        else:
            card_layout.setContentsMargins(16, 16, 16, 16)

        if heading and subheading:
            theme_label = QLabel(
                f"<div style='font-size:13px; margin-bottom:2px'> {heading} </div>"
                f""" <div style='font-size:11px; color: {Palette().get_palette_role().subtext};'>
                {subheading} </div>"""
            )

            card_layout.addWidget(theme_label)

        return card_layout, card_frame

    def adaptive_icon(self, icon_code: dict[str, str], size: int) -> QLabel:
        """Adaptive icon supporting fluent and material icons."""
        winver = Utility().get_windows_version()
        fluent_support = 11
        mdl2_support = 10
        font = None

        if winver == fluent_support:
            font = QFont("Segoe Fluent Icons", size)
        elif winver == mdl2_support:
            font = QFont("Segoe MDL2 Assets", size)

        icon = QLabel()
        if winver in (fluent_support, mdl2_support):
            icon.setFont(font)
            icon.setText(icon_code.get("code_glyph"))
            icon.setStyleSheet("background-color: transparent;")
        else:
            material_size = size + 8
            qicon = icons.get_icon(icon_code.get("material_path"))
            icon.setPixmap(qicon.pixmap(QSize(material_size, material_size)))
            icon.setStyleSheet("background-color: transparent;")

        return icon

    def setting_combobox(self):
        """Setting combobox template."""
        setting_combobox = SettingCombobox()
        setting_combobox.setFixedWidth(164)
        setting_combobox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        return setting_combobox

    def setting_button(self):
        """Setting button template."""
        setting_button = QPushButton()
        setting_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        setting_button.setFixedWidth(164)

        return setting_button

    def setting_header_label(self):
        """Setting header label template."""
        setting_header_font = QFont()
        setting_header_font.setBold(True)
        setting_header_font.setPixelSize(13)

        setting_header_label = QLabel()
        setting_header_label.setFont(setting_header_font)
        setting_header_label.setContentsMargins(0, 0, 0, 4)

        return setting_header_label

    def setting_switch(self):
        """Toggle switch template for setting."""
        palett_comp = Palette()
        palette = palett_comp.get_palette()
        accent = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Accent)
        text = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        inverted_text = palett_comp.invert_color(text)
        window = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window)

        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        widget.setLayout(layout)

        label = QLabel()
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignRight)

        switch = PlCheckBox()
        switch._checkedBackgroundColor = accent  # pylint: disable=W0212
        switch._checkedHandleColor = inverted_text  # pylint: disable=W0212
        switch.backgroundColor = window
        switch.update()
        layout.addWidget(switch)

        def switch_event():
            """Change switch label based on check state."""
            if switch.isChecked():
                label.setText("On")
            else:
                label.setText("Off")

        switch.toggled.connect(switch_event)
        switch_event()

        return widget, switch

    def bread_crumb_bar(self, stack_widget: QStackedWidget):
        """Bread crumb inspired by WinUi3."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget.setLayout(layout)

        index_list = []

        def stack_change_event(is_start: bool = False):
            """Change breadcrumb based on index."""
            nonlocal index_list

            stack_index = stack_widget.currentIndex()
            object_name = stack_widget.currentWidget().objectName()
            title_name = object_name.replace("-", " ").replace("_", " ").title()

            new_title = self.bread_crumb_title(title_name, is_start)
            new_title.mousePressEvent = lambda _: stack_widget.setCurrentIndex(stack_index)

            if stack_index not in index_list:
                index_list.append(stack_index)
                layout.addWidget(new_title)
                title_list = widget.findChildren(QLabel, "breadCrumbTitle")
            else:
                deleted_widget_count = len(index_list[index_list.index(stack_index) + 1 :])
                del index_list[-deleted_widget_count:]

                for _ in range(deleted_widget_count):
                    item = layout.takeAt(layout.count() - 1).widget()
                    item.deleteLater()

                title_list = widget.findChildren(QLabel, "breadCrumbTitle")
                del title_list[-deleted_widget_count:]
                title_list[-1].setDisabled(True)

            for title in title_list[:-1]:
                title.setEnabled(True)

        # Start index
        stack_change_event(is_start=True)

        stack_widget.currentChanged.connect(lambda: stack_change_event(is_start=False))

        return widget

    def bread_crumb_title(self, title_name: str, is_start: bool = False):
        """Bread crumb title widget."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        widget.setLayout(layout)

        if not is_start:
            chevron = SettingTemplate().adaptive_icon(icons.fluent_chevron_right, 8)
            layout.addWidget(chevron, alignment=Qt.AlignmentFlag.AlignCenter)

        palette = Palette().get_palette()
        text_active = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        text_disabled = palette.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text)

        font = QFont()
        font.setBold(True)
        font.setPixelSize(20)

        title = QLabel()
        title.setObjectName("breadCrumbTitle")
        title.setFont(font)
        title.setText(title_name)
        title.setContentsMargins(8, 8, 8, 8)
        title.setStyleSheet(
            f"QLabel {{ color: {text_disabled.name()}; }}"
            f"QLabel:disabled {{ color: {text_active.name()} }}"
        )
        title.setDisabled(True)
        title.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(title)

        return widget


class SettingUI:
    """Setting UI."""

    def __init__(self):
        # Composition
        self.setting_core = SettingCore()
        self.setting_template = SettingTemplate()
        self.utility = Utility()

    # ------------------------------ Window ------------------------------
    def setting_window(self, parent):
        """Setting window."""
        settings_window = QDialog(parent)
        settings_window.setWindowTitle("Settings")
        geometry = Styling().get_geometry(parent, 600, 400)
        settings_window.setGeometry(geometry)
        settings_window.setWindowIcon(QIcon(constant.icon_path))
        Styling().apply_mica(settings_window)

        setting_layout = QVBoxLayout(settings_window)
        setting_layout.setSpacing(0)
        setting_layout.setContentsMargins(12, 0, 12, 12)

        setting_stack = QStackedWidget()
        setting_stack.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("settings")
        scroll_area.setStyleSheet("#settings {background-color: transparent;}")
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        setting_stack.addWidget(scroll_area)

        # Add widget to stack widget first before calling bread crumb
        setting_layout.addWidget(self.setting_template.bread_crumb_bar(setting_stack))
        setting_layout.addWidget(setting_stack)

        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("#contentWidget {background-color: transparent;}")
        scroll_area.setWidget(content_widget)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(8, 8, 8, 8)

        # Pro Version
        if Utility().program_name != "KeyTik Pro":
            content_layout.addWidget(self.pro_version())

        # Appearance
        content_layout.addWidget(SettingAppearance().appearance(settings_window))

        # General
        content_layout.addWidget(SettingGeneral(settings_window).general(settings_window))

        # Advanced
        content_layout.addWidget(SettingInstallation().installation())

        # About
        content_layout.addWidget(SettingAbout(setting_stack).about())

        settings_window.exec()

    # ------------------------------ Pro Version ------------------------------
    def pro_version(self):
        """Pro version setting."""
        pro_version_widget = QWidget()
        pro_version_layout = QVBoxLayout(pro_version_widget)
        pro_version_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        pro_version_label = self.setting_template.setting_header_label()
        pro_version_label.setText("Pro Version")
        pro_version_layout.addWidget(pro_version_label)

        # Upgrade to Pro Version
        pro_upgrade_button = self.setting_template.setting_button()
        pro_upgrade_button.setText("Get KeyTik Pro")
        pro_upgrade_button.clicked.connect(
            lambda: webbrowser.open("https://fajarrahmadjaya.gumroad.com/l/keytik-pro")
        )
        pro_upgrade_button.setObjectName(Styling().button_highlight())

        pro_upgrade_layout, pro_upgrade_frame = self.setting_template.setting_card(
            heading="KeyTik Pro", subheading="Pro version available at $20"
        )
        pro_upgrade_layout.addWidget(pro_upgrade_button)
        pro_version_layout.addWidget(pro_upgrade_frame)

        return pro_version_widget


class SettingAppearance:
    """Appearance section on setting."""

    def __init__(self):
        self.setting_template = SettingTemplate()
        self.setting_core = SettingCore()

        # Cache
        self.circle_cache = {}

    def appearance(self, settings_window):
        """Appearance setting."""
        appearance_widget = QWidget()
        appearance_layout = QVBoxLayout(appearance_widget)
        appearance_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        appearance_label = self.setting_template.setting_header_label()
        appearance_label.setText("Appearance")
        appearance_layout.addWidget(appearance_label)

        # Style
        appearance_layout.addWidget(self.style())

        # Theme
        appearance_layout.addWidget(self.theme(settings_window))

        # Accent
        appearance_layout.addWidget(self.accent(settings_window))

        # Mica Effect
        if Styling().MICA_SUPPORTED:
            appearance_layout.addWidget(self.mica_effect(settings_window))

        return appearance_widget

    def style(self):
        """Style Widget."""
        style_combobox = self.setting_template.setting_combobox()
        style_combobox.addItem("Default")
        style_combobox.addItems(QStyleFactory.keys())
        current_style = Config().get_config().style
        style_combobox.setCurrentText(current_style if current_style else "Default")
        style_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_style(updated_style=style_combobox.currentText())
        )

        style_layout, style_frame = self.setting_template.setting_card(
            heading="Style", subheading="Change widget style"
        )
        style_layout.addWidget(style_combobox)

        return style_frame

    def theme(self, settings_window):
        """Theme Widget."""
        theme_combobox = self.setting_template.setting_combobox()

        # Default theme
        theme_combobox.addItem("Light", {"type": "default", "value": "light"})
        theme_combobox.addItem("Dark", {"type": "default", "value": "dark"})
        theme_combobox.addItem("System", {"type": "default", "value": "system"})

        # Custom theme
        for custom_theme in self.setting_core.get_custom_theme():
            theme_name = custom_theme.replace(".json", "")
            theme_combobox.addItem(
                theme_name.replace("_", " ").title(),
                {"type": "custom", "value": theme_name},
            )

        # qt-themes theme
        qt_themes_dict = qt_themes.get_themes()
        for qt_theme, _ in qt_themes_dict.items():
            # Remove catppuccin
            if not qt_theme.startswith("catppuccin") or not qt_theme.startswith("dracula"):
                theme_combobox.addItem(
                    qt_theme.replace("_", " ").title(),
                    {"type": "qt-themes", "value": qt_theme},
                )

        theme_combobox.setCurrentText(Config().get_config().theme.replace("_", " ").title())
        theme_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_theme(
                theme=theme_combobox.currentData(), parent=settings_window
            )
        )

        theme_layout, theme_frame = self.setting_template.setting_card(
            heading="Theme", subheading="Change widget palette"
        )
        theme_layout.addWidget(theme_combobox)

        return theme_frame

    def accent(self, settings_window):
        """Theme Widget."""
        config = Config().get_config()
        accent_combobox = self.setting_template.setting_combobox()
        accent_combobox.view().setFixedWidth(200)

        # Item data should be the color name and color hex
        accent_combobox.addItem("Default", ["Default", "default"])
        # Dracula accent
        accent_combobox.addItem(self.color_circle("#BD93F9"), "Dracula", ["Dracula", "#BD93F9"])
        # Catppuccin Accent
        for flavor in catppuccin_palette:
            for color in flavor.colors:
                if color.accent:
                    accent_name = f"Catppuccin {flavor.name} {color.name}".title()
                    accent_combobox.addItem(
                        self.color_circle(color.hex),
                        accent_name,
                        [accent_name, color.hex],
                    )

                if color.hex == config.accent:
                    accent_name = f"Catppuccin {flavor.name} {color.name}".title()
                    accent_combobox.setCurrentText(accent_name)

        accent_combobox.setCurrentText(Config().get_config().accent.title())
        accent_combobox.setToolTip(accent_combobox.currentText())
        accent_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_accent(
                accent=accent_combobox.currentData(), parent=settings_window
            )
        )

        accent_layout, accent_frame = self.setting_template.setting_card(
            heading="Accent Color", subheading="Change highlighted widget color"
        )
        accent_layout.addWidget(accent_combobox)

        return accent_frame

    def color_circle(self, color_hex):
        """Circle showing accent color."""
        if color_hex in self.circle_cache:
            return self.circle_cache[color_hex]

        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color_hex))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 16, 16)
        painter.end()
        icon = QIcon(pixmap)
        self.circle_cache[color_hex] = icon

        return icon

    def mica_effect(self, settings_window):
        """Mica Effect Widget."""
        mica_combobox = self.setting_template.setting_combobox()
        mica_combobox.addItems(["Default", "Alt", "Disable"])
        mica_combobox.setCurrentText(Config().get_config().mica_effect.capitalize())
        mica_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_mica_effect(
                new_mica=mica_combobox.currentText(), parent=settings_window
            )
        )

        mica_layout, mica_frame = self.setting_template.setting_card(
            heading="Mica Effect", subheading="Windows and surfaces appear translucent"
        )
        mica_layout.addWidget(mica_combobox)

        return mica_frame


class SettingGeneral:
    """General section on setting."""

    def __init__(self, settings_window: QDialog):
        self.setting_template = SettingTemplate()
        self.setting_core = SettingCore()
        self.settings_window = settings_window

    def general(self, settings_window):
        """General setting."""
        general_widget = QWidget()
        general_layout = QVBoxLayout(general_widget)
        general_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        general_label = self.setting_template.setting_header_label()
        general_label.setText("General")
        general_layout.addWidget(general_label)

        # Profile Location
        general_layout.addWidget(self.profile_location(settings_window))

        # Announcement
        general_layout.addWidget(self.announcement(settings_window))

        # Auto Complete
        general_layout.addWidget(self.auto_complete())

        # Peek script
        general_layout.addWidget(self.enable_peek())

        return general_widget

    def profile_location(self, settings_window):
        """Profile Location Widget."""
        profile_location_button = self.setting_template.setting_button()
        profile_location_button.setText("Change Location")
        profile_location_button.clicked.connect(
            lambda: self.setting_core.change_data_location(settings_window)
        )

        profile_location_layout, profile_location_frame = self.setting_template.setting_card()

        profile_dir = Config().get_config().profile_path
        theme_label = QLabel(
            "<div style='font-size:13px; margin-bottom:2px'>Profile Location</div>"
            "<div style='font-size:11px;'>"
            f"<a href='subheading_click'> {profile_dir} </a>"
            "</div>"
        )
        theme_label.setTextFormat(Qt.RichText)
        theme_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        theme_label.setOpenExternalLinks(False)
        theme_label.linkActivated.connect(lambda: os.startfile(profile_dir))
        profile_location_layout.addWidget(theme_label)

        profile_location_layout.addWidget(profile_location_button)

        return profile_location_frame

    def announcement(self, settings_window):
        """Announcement Widget."""
        announcement = Announcement()  # Composition
        announcement_button = self.setting_template.setting_button()
        announcement_button.setText("Announcement")
        announcement_button.clicked.connect(
            lambda: announcement.show_announcement_window(settings_window)
        )

        announcement_layout, announcement_frame = self.setting_template.setting_card(
            heading="Announcement", subheading="Show announcement"
        )
        announcement_layout.addWidget(announcement_button)

        return announcement_frame

    def auto_complete(self):
        """Entry auto complete widget."""
        auto_complete_combobox = self.setting_template.setting_combobox()

        # Item
        auto_complete_combobox.addItem("Disable", "disable")
        auto_complete_combobox.addItem("Inline", "inline")
        auto_complete_combobox.addItem("Pop Up", "popup")
        auto_complete_combobox.addItem("Unfiltered Pop UP", "unfiltered_popup")

        current_text = auto_complete_combobox.findData(Config().get_config().auto_complete)
        auto_complete_combobox.setCurrentIndex(current_text)
        auto_complete_combobox.currentTextChanged.connect(
            lambda: self.setting_core.save_auto_complete(auto_complete_combobox.currentData())
        )

        auto_complete_layout, auto_complete_frame = self.setting_template.setting_card(
            heading="Input Auto Complete", subheading="Enable/Disable key input auto complete"
        )
        auto_complete_layout.addWidget(auto_complete_combobox)

        return auto_complete_frame

    def enable_peek(self):
        """Enable script peek widget."""
        is_enabled = Config().get_config().enable_peek

        widget, switch = self.setting_template.setting_switch()
        switch.setChecked(is_enabled)
        switch.toggled.connect(
            lambda: self.setting_core.save_enable_peek(switch.isChecked(), self.settings_window)
        )

        layout, frame = self.setting_template.setting_card(
            heading="Enable script peek", subheading="Enable button to see profile script."
        )
        layout.addWidget(widget)

        return frame


class SettingInstallation:
    """Installation section on setting."""

    def __init__(self):
        self.setting_template = SettingTemplate()
        self.setting_core = SettingCore()

    def installation(self):
        """Advanced setting."""
        installation_widget = QWidget()
        installation_layout = QVBoxLayout(installation_widget)
        installation_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        installaation_label = self.setting_template.setting_header_label()
        installaation_label.setText("Installation")
        installation_layout.addWidget(installaation_label)

        # AutoHotkey Installation
        installation_layout.addWidget(self.ahk_installation())

        # Interception Driver Installation
        installation_layout.addWidget(self.interception_installation())

        return installation_widget

    def ahk_installation(self):
        """AutoHotkey Installation Widget."""
        ahk_installed = os.path.exists(Utility().ahkv2_dir)

        ahk_button = self.setting_template.setting_button()
        ahk_button.setText("Uninstall AutoHotkey" if ahk_installed else "Install AutoHotkey")
        ahk_button.clicked.connect(lambda: self.setting_core.ahk_action(ahk_installed))

        ahk_layout, ahk_frame = self.setting_template.setting_card(
            heading="AutoHotkey Installation",
            subheading=("AutoHotkey is installed" if ahk_installed else "AutoHotkey not installed"),
        )
        ahk_layout.addWidget(ahk_button)

        return ahk_frame

    def interception_installation(self):
        """Interception Driver Installation."""
        interception_installed = os.path.exists(constant.DRIVER_PATH)

        interception_button = self.setting_template.setting_button()
        interception_button.setText(
            "Uninstall Interception Driver"
            if interception_installed
            else "Install Interception Driver"
        )
        interception_button.clicked.connect(
            lambda: self.setting_core.driver_action(interception_installed)
        )

        interception_layout, interception_frame = self.setting_template.setting_card(
            heading="Interception Driver Installation",
            subheading=(
                "Interception Driver is Installed"
                if interception_installed
                else "Interception Driver not Installed"
            ),
        )
        interception_layout.addWidget(interception_button)

        return interception_frame


class SettingAbout:
    """About section on setting."""

    def __init__(self, setting_stack: QStackedWidget = None):
        self.setting_template = SettingTemplate()

        self.setting_stack = setting_stack

    def about(self):
        """About section."""
        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        about_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        installaation_label = self.setting_template.setting_header_label()
        installaation_label.setText("About")
        about_layout.addWidget(installaation_label)

        # Check for Update
        about_layout.addWidget(self.version())

        # Changelog
        about_layout.addWidget(self.changelog())

        # Unreleased Changelog
        about_layout.addWidget(self.unreleased_changelog())

        # Third party open-source licenses
        about_layout.addWidget(self.open_source_licenses())

        return about_widget

    def version(self):
        """Check for Update Widget."""
        layout, frame = self.setting_template.setting_card(
            heading="Version", subheading=Utility().current_version
        )

        button = self.setting_template.setting_button()
        button.setText("Check For Updates")

        def button_event():
            """Check for update."""
            data = Data().get_data()
            latest_version = data.latest_version

            if latest_version != Utility().current_version:
                self.update_changelog()
            else:
                QMessageBox.information(
                    QApplication.activeWindow(),
                    "Check For Update",
                    "You are using the latest version of KeyTik.",
                )

        button.clicked.connect(button_event)
        layout.addWidget(button)

        return frame

    def changelog(self):
        """Changelog Widget."""
        changelog_layout, changelog_frame = self.setting_template.setting_card(
            heading="What's New", subheading="Show changelog"
        )

        button = self.setting_template.setting_button()
        button.setText("Changelog")
        button.clicked.connect(lambda: self.update_changelog(ischangelog=True))
        changelog_layout.addWidget(button)

        return changelog_frame

    def unreleased_changelog(self):
        """What's coming widget."""
        changelog_layout, changelog_frame = self.setting_template.setting_card(
            heading="What's Coming", subheading="Show nightly/upcoming update changelog"
        )

        button = self.setting_template.setting_button()
        button.setText("Upcoming Changelog")

        def button_event():
            """Fetch changelog generated by git-cliff action."""
            version, changelog_md = SettingCore().get_unreleased_changlog()
            self.update_changelog(version, changelog_md, ischangelog=True, unreleased=True)

        button.clicked.connect(button_event)
        changelog_layout.addWidget(button)

        return changelog_frame

    def update_changelog(
        self, new_version=None, changelog_md=None, ischangelog=False, unreleased=False
    ):
        """Show update changelog window."""
        parent = QApplication.activeWindow()
        if not new_version and not changelog_md:
            data = Data().get_data()
            new_version = data.latest_version
            changelog_md = data.changelog

        window = QDialog(parent)
        utility = Utility()
        if unreleased:
            window.setWindowTitle("Upcoming Changelog")
        elif new_version != utility.current_version:
            window.setWindowTitle(f"New version of {utility.program_name} is available")
        else:
            window.setWindowTitle("Changelog")
        window.setGeometry(Styling().get_geometry(parent, 520, 360))
        window.setWindowIcon(QIcon(constant.icon_path))
        Styling().apply_mica(window)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        window.setLayout(layout)

        layout.addWidget(self.changelog_text(unreleased, new_version, changelog_md))

        button_widget = QWidget()
        button_widget.setMaximumHeight(32)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(16, 0, 16, 0)
        button_layout.setSpacing(32)
        button_widget.setLayout(button_layout)

        button_layout.addWidget(self.update_button(window))
        button_layout.addWidget(self.skip_button(new_version, window))

        if not ischangelog:
            layout.addWidget(button_widget)

        window.exec()

    def changelog_text(
        self,
        unreleased: bool,
        new_version: str = "(Failed to fetch latest version)",
        changelog_md: str = "Failed to fetch changelog",
    ):
        """Return changelog text edit."""
        text_edit = QTextEdit()
        text_edit.setObjectName("ChangelogText")
        text_edit.setReadOnly(True)
        text_edit.document().setDocumentMargin(8)
        text_edit.document().setIndentWidth(20)

        if Config().get_config().mica_effect != "disable" and Styling().MICA_SUPPORTED:
            text_edit.setStyleSheet(
                f"#ChangelogText {{background-color: {Palette().get_palette_role().base_rgba}}}"
            )

        version_indicator = "Latest" if not unreleased else "Upcoming"
        text_edit.setMarkdown(
            "## What's Changed\n\n"
            f"`{version_indicator}: {new_version} - Current: {Utility().current_version}`\n"
            "\n---\n\n"
            f"{changelog_md.replace('## Changelog', '')}"
        )

        return text_edit

    def update_button(self, window: QDialog):
        """Retrun update button opening update link."""
        button = QPushButton()
        button.setObjectName(Styling().button_highlight())
        button.setText("Update now")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        def button_event():
            """Open release in web browser and close dialog."""
            webbrowser.open(diff.RELEASE_LINK)
            window.accept()

        button.clicked.connect(button_event)

        return button

    def skip_button(self, new_version: str, window: QDialog):
        """Return skip button appending new version to skip version config."""
        button = QPushButton()
        button.setText("Skip This Version")
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        def button_event():
            """Save current version to skip version config."""
            try:
                config = Config().get_config()

                # Update config
                config.skip_update = new_version
                Config().update_config(config)

                window.reject()

            except FileNotFoundError as error:
                print(f"Error: {error}")
                window.reject()

        button.clicked.connect(button_event)

        return button

    def open_source_licenses(self):
        """Third party open-source licenses widget."""
        button = QPushButton()
        button.setFlat(True)
        button.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        card_layout, card_frame = self.setting_template.setting_card(
            heading="Open-Source licenses", subheading="See third party licenses."
        )
        layout.addWidget(card_frame)

        right_chevron = SettingTemplate().adaptive_icon(icons.fluent_chevron_right, 10)
        right_chevron.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        card_layout.addWidget(right_chevron)

        license_index = None

        def button_event():
            """Add widget to stack widget and move the index there."""
            nonlocal license_index

            if not license_index:
                license_widget = self.licenses_widget()
                self.setting_stack.addWidget(license_widget)
                self.setting_stack.setCurrentIndex(self.setting_stack.indexOf(license_widget))
                license_index = self.setting_stack.indexOf(license_widget)

                license_text = QTextEdit()
                license_text.setReadOnly(True)
                self.setting_stack.addWidget(license_text)
            else:
                self.setting_stack.setCurrentIndex(license_index)

        button.setFixedHeight(card_frame.sizeHint().height())
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.clicked.connect(button_event)

        return button

    def licenses_widget(self):
        """Display open-source licenses used."""
        scroll_area = QScrollArea()
        scroll_area.setObjectName("open-source-licenses")
        scroll_area.setStyleSheet("#open-source-license {background-color: transparent;}")
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)

        widget = QWidget()
        widget.setObjectName("licensesWidget")
        widget.setStyleSheet("#licensesWidget {background-color: transparent;}")
        scroll_area.setWidget(widget)

        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        widget.setLayout(layout)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(content_widget)

        header = self.setting_template.setting_header_label()
        header.setText("Open-Source Licenses")
        content_layout.addWidget(header)

        try:
            with open(constant.open_source_license_path, encoding="utf8") as file:
                content: list[dict] = json.load(file)
        except (FileNotFoundError, ValueError) as error:
            print(f"Error while opening {constant.open_source_license_path}: {error}")
            content = {}

        for lib in content:
            content_layout.addWidget(self.license_card(lib))

        return scroll_area

    def license_card(self, lib: dict[str, str]):
        """Setting card with pill."""
        button = QPushButton()
        button.setFlat(True)
        button.setStyleSheet("background-color: transparent;")

        layout = QVBoxLayout(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.NoFrame)
        frame.setObjectName("setting")
        frame.setStyleSheet(Styling().card("setting"))
        layout.addWidget(frame)

        card_layout = QGridLayout()
        card_layout.setContentsMargins(16, 8, 16, 8)
        card_layout.setVerticalSpacing(8)
        card_layout.setHorizontalSpacing(0)
        frame.setLayout(card_layout)

        card_layout.addWidget(
            self.license_label(lib.get("Name"), lib.get("Author"), lib.get("Version")), 0, 0
        )

        card_layout.addWidget(self.license_pill(lib.get("License")), 1, 0)

        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedHeight(frame.sizeHint().height())

        def button_event():
            """Show license text."""
            license_text_widget: QTextEdit = self.setting_stack.widget(
                self.setting_stack.currentIndex() + 1
            )
            license_text_widget.setObjectName(lib.get("Name"))
            license_text_widget.setText(lib.get("LicenseText"))
            self.setting_stack.setCurrentIndex(self.setting_stack.indexOf(license_text_widget))

        button.clicked.connect(button_event)

        return button

    def license_label(self, package: str, author: str, version: str):
        """Third party open-source license QLable."""
        label_widget = QWidget()
        label_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        label_layout = QGridLayout()
        label_layout.setVerticalSpacing(2)
        label_layout.setHorizontalSpacing(0)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_widget.setLayout(label_layout)

        heading_font = QFont()
        heading_font.setPixelSize(13)

        package_name = QLabel()
        package_name.setFont(heading_font)
        package_name.setStyleSheet("background-color: transparent;")
        package_name.setText(package)
        label_layout.addWidget(package_name, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)

        version_number = QLabel()
        version_number.setFont(heading_font)
        version_number.setStyleSheet("background-color: transparent;")
        version_number.setText(version)
        label_layout.addWidget(version_number, 0, 1, alignment=Qt.AlignmentFlag.AlignRight)

        subheading_font = QFont()
        subheading_font.setPixelSize(11)

        author_name = QLabel()
        author_name.setFont(subheading_font)
        author_name.setStyleSheet(
            f"background-color: transparent;color: {Palette().get_palette_role().subtext}"
        )
        author_name.setText(author)
        label_layout.addWidget(author_name, 1, 0, alignment=Qt.AlignmentFlag.AlignLeft)

        # theme_label = QLabel(
        #     f"<div style='font-size:13px; margin-bottom:2px'> {package} </div>"
        #     f""" <div style='font-size:11px; color: {Palette().get_palette_role().subtext};'>
        #     {author} </div>"""
        # )

        # card_layout.addWidget(theme_label, 0, 0)

        # right_chevron = SettingTemplate().adaptive_icon(icons.fluent_chevron_right, 10)
        # right_chevron.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        # card_layout.addWidget(right_chevron, 0, 1, 2, 1)

        return label_widget

    def license_pill(self, license_name: str):
        """Third party open-source license pill."""
        palette_comp = Palette()
        palette = palette_comp.get_palette()
        alternate_base = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.AlternateBase)
        text = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        invert_text = palette_comp.invert_color(text)

        pill = QFrame()
        pill.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        pill_layout = QHBoxLayout()
        pill_layout.setContentsMargins(4, 2, 4, 2)
        pill_layout.setSpacing(0)
        pill_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill.setLayout(pill_layout)

        license_font = QFont()
        license_font.setPixelSize(10)

        license_label = QLabel()
        license_label.setFont(license_font)
        license_label.setText(license_name)
        license_label.setStyleSheet(f"color: {invert_text.name()}")

        pill_layout.addWidget(license_label)

        pill.setStyleSheet(
            f"background-color: {alternate_base.name()};"
            f"border-radius: {pill.sizeHint().height() / 2}px;"
        )

        return pill
