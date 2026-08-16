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

"""UI for create/edit profile."""

import os

from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import QFont, QIcon, QPalette  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from keytik.profile_manager.parse_script import ParseScript
from keytik.profile_manager.write_script import WriteDefault, WriteScript
from keytik.profile_mode.default_mode import DefaultMode
from keytik.profile_mode.shared_row import SharedRow
from keytik.profile_mode.shortcut_row import ShortcutRow
from keytik.profile_mode.text_mode import TextMode
from keytik.select_device.select_device import SelectDevice
from keytik.select_program.select_program_ui import SelectProgramUI
from keytik.setting.setting_ui import SettingTemplate
from keytik.utility import constant, diff, icons
from keytik.utility.style import Palette, Styling


class ProfileUI:
    """Create/edit profile UI."""

    def __init__(self, main_core):
        # Parameter
        self.main_core = main_core

        # Composition
        # Used for save change since it need for
        # current remap row composition (Mode changed or edit middle)
        self.default_mode_comp = None
        self.shortcut_row_comp = None

        # UI
        self.edit_window = None
        self.edit_frame = QWidget()
        self.edit_frame_layout = QVBoxLayout(self.edit_frame)
        self.middle_stack = None

    def edit_script(self, script_name: str, parent):
        """Create/edit profile window."""
        self.edit_window = QDialog(parent)
        # Handle Create New Profile
        if not script_name:
            script_path = None
            lines = ["; default\n"]

            self.edit_window.setWindowTitle("Create New Profile")
        # Handle Edit Profile
        else:
            script_path = os.path.join(self.main_core.script_dir, script_name)
            with open(script_path, encoding="utf-8") as file:
                lines = file.readlines()
            if not lines:
                return

            self.edit_window.setWindowTitle(f"Edit {script_name.replace('.ahk', '').title()}")

        first_line = lines[0].strip()

        self.edit_window.setWindowIcon(QIcon(constant.icon_path))
        geometry = Styling().get_geometry(parent, 640, 480)
        self.edit_window.setGeometry(geometry)
        Styling().apply_mica(self.edit_window)

        edit_layout = QVBoxLayout(self.edit_window)
        edit_layout.setObjectName("editLayout")
        edit_layout.setContentsMargins(0, 0, 0, 0)

        # Middle part of profile manager
        self.middle_stack = QStackedWidget()

        self.middle_stack.addWidget(self.scroll_area())

        text_block = TextMode().text_mode_widget(self.edit_window, self.edit_frame, lines)
        self.middle_stack.addWidget(text_block)

        self.middle_stack.addWidget(self.profile_setting(script_name, lines))
        edit_layout.addWidget(self.middle_stack)

        # Add profile mode widget
        index = diff.mode_map.get(lines[0].strip().lower())
        self.build_profile(index, lines=lines)

        edit_layout.addWidget(self.command_bar(first_line))

        self.edit_window.setLayout(edit_layout)
        self.edit_window.exec()

    def command_bar(self, first_line: str):
        """Command bar inspired by WinUI3."""
        widget = QWidget()
        widget.setObjectName("commandBar")
        widget.setStyleSheet("#commandBar { background-color: rgba(0, 0, 0, 0.08); }")  # 1C1C1C

        layout = QHBoxLayout()
        layout.setContentsMargins(32, 0, 32, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget.setLayout(layout)

        # Content
        content_widget = self.content(first_line)
        layout.addWidget(content_widget)

        # Primary command
        layout.addWidget(self.primary_command(content_widget.findChild(QComboBox)))

        return widget

    def content(self, first_line):
        """Command bar content."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget.setLayout(layout)

        combobox = QComboBox(self.edit_window)
        combobox.addItems(diff.mode_item)
        combobox.setEditable(True)
        combobox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignLeft)
        combobox.lineEdit().setReadOnly(True)
        combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        default_index = diff.mode_map.get(first_line.lower(), 0)
        combobox.setCurrentIndex(default_index)
        combobox.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        combobox.setMinimumHeight(32)
        combobox.setMinimumWidth(180)
        combobox.currentIndexChanged.connect(self.build_profile)
        combobox.setStyleSheet(f"""
            QComboBox {{
                background-color: transparent;
            }}

            QComboBox QAbstractItemView {{
                background-color: {
            Palette()
            .get_palette()
            .color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window)
            .name()
        };
            }}
        """)
        layout.addWidget(combobox)

        return widget

    def primary_command(self, combobox: QComboBox):
        """Command bar primary command."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget.setLayout(layout)

        setting_button = self.app_bar_icon(
            fluent_icon=icons.fluent_setting, button_text="Profile Setting"
        )
        setting_button.setCheckable(True)

        prev_stack_index = 0

        def setting_event():
            """Profile setting click event."""
            nonlocal prev_stack_index
            if setting_button.isChecked():
                prev_stack_index = self.middle_stack.currentIndex()
                self.middle_stack.setCurrentIndex(2)
            else:
                self.middle_stack.setCurrentIndex(prev_stack_index)

        setting_button.clicked.connect(setting_event)
        layout.addWidget(setting_button)

        save_button = self.app_bar_icon(fluent_icon=icons.fluent_save, button_text="Save Profile")

        save_button.clicked.connect(
            lambda: self.save_changes(
                combobox.currentText().strip().lower(), self.middle_stack.widget(2)
            )
        )
        layout.addWidget(save_button)

        return widget

    def app_bar_icon(self, fluent_icon: dict[str, str], button_text: str):
        """Button  inspired by WinUI3."""
        button = QPushButton()
        button.setFlat(True)
        button.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(button)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(SettingTemplate().adaptive_icon(fluent_icon, 12))

        text = QLabel()
        text.setText(button_text)
        layout.addWidget(text)

        button.setMinimumSize(layout.sizeHint())

        return button

    def profile_setting(self, script_name: str, lines: list[str]):
        """Profile setting."""
        setting_template = SettingTemplate()
        parse_script = ParseScript()

        widget = QWidget()

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(0)
        widget.setLayout(layout)

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPixelSize(20)

        title = QLabel()
        title.setText("Profile Settings")
        title.setFont(title_font)
        title.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("profileSettingScroll")
        scroll_area.setStyleSheet("#profileSettingScroll {background-color: transparent;}")
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        scroll_widget = QWidget()
        scroll_widget.setObjectName("profileScrollContent")
        scroll_widget.setStyleSheet("#profileScrollContent {background-color: transparent;}")
        scroll_area.setWidget(scroll_widget)

        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(8, 8, 8, 8)

        scroll_layout.addWidget(self.profile_name(script_name))

        scroll_layout.addWidget(self.profile_device(setting_template, lines, parse_script))

        scroll_layout.addWidget(self.profile_program(setting_template, lines, parse_script))

        scroll_layout.addWidget(self.profile_no_tray(setting_template, lines))

        return widget

    def profile_setting_card(self, header_text: str, icon_code: dict[str, str]):
        """Profile setting profile name."""
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setObjectName("profileCard")
        frame.setStyleSheet(Styling().card("profileCard"))
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 16, 16, 16)
        layout.setSpacing(20)
        frame.setLayout(layout)

        if icon_code:
            layout.addWidget(SettingTemplate().adaptive_icon(icon_code, 16))

        content_widget = QWidget()
        layout.addWidget(content_widget)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        content_widget.setLayout(content_layout)

        header_font = QFont()
        header_font.setPixelSize(13)

        header = QLabel()
        header.setText(header_text)
        header.setFont(header_font)
        header.setStyleSheet("background-color: transparent;")
        content_layout.addWidget(header)

        entry = QLineEdit()
        entry.setMinimumHeight(28)
        entry.setMaximumWidth(320)
        content_layout.addWidget(entry)

        return frame

    def profile_name(self, script_name: str):
        """Profile name on profile setting."""
        widget = self.profile_setting_card("Profile Name", icons.fluent_label)
        entry = widget.findChild(QLineEdit)
        if script_name:
            entry.setText(script_name.replace(".ahk", ""))
            entry.setReadOnly(True)
        else:
            entry.setText("")
            entry.setReadOnly(False)
        entry.setObjectName("ScriptNameEntry")

        return widget

    def profile_device(
        self, setting_template: SettingTemplate, lines: list[str], parse_script: ParseScript
    ):
        """Bind to device setting widget."""
        widget = self.profile_setting_card(
            "Bind Profile to Keyboards or Mouses", icons.fluent_input
        )

        entry = widget.findChild(QLineEdit)
        entry.setObjectName("KeyboardEntry")
        device_line = parse_script.parse_device(lines) if lines else None
        entry.setText(device_line)

        button = setting_template.setting_button()

        button.setText("Add Device")
        button.setObjectName(Styling().button_highlight())
        button.setMaximumHeight(32)
        button.clicked.connect(
            lambda: SelectDevice().open_device_selection(self.edit_window, entry)
        )

        widget.layout().addWidget(button)

        return widget

    def profile_program(
        self, setting_template: SettingTemplate, lines: list[str], parse_script: ParseScript
    ):
        """Bind to program setting widget."""
        widget = self.profile_setting_card("Bind Profile to Programs", icons.fluent_apps)

        entry = widget.findChild(QLineEdit)
        entry.setObjectName("ProgramEntry")
        program_line = parse_script.parse_program(lines) if lines else None
        entry.setText(program_line)

        button = setting_template.setting_button()
        button.setText("Add Program")
        button.setObjectName(Styling().button_highlight())
        button.setMaximumHeight(32)
        button.clicked.connect(lambda: SelectProgramUI().program_window(entry, self.edit_window))

        widget.layout().addWidget(button)

        return widget

    def profile_no_tray(self, setting_template: SettingTemplate, lines: list[str]):
        """Profile no tray setting."""
        layout, widget = setting_template.setting_card(
            heading="No Tray Icon",
            subheading="Hide profile from system tray hidden icons.",
            icon_code=icons.fluent_hide,
        )
        switch_widget, switch = setting_template.setting_switch()
        switch.setObjectName("noTrayCheckbox")

        for line in lines:
            if line.startswith("#NoTrayIcon"):
                switch.setChecked(True)
                break

        layout.addWidget(switch_widget)

        return widget

    def scroll_area(self):
        """Scroll area with expand button."""
        widget = QWidget()
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        widget.setLayout(layout)

        edit_scroll = QScrollArea(self.edit_window)
        layout.addWidget(edit_scroll, 0, 0, 1, 2)
        edit_scroll.setWidgetResizable(True)
        edit_scroll.setFrameShape(QFrame.NoFrame)
        edit_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        edit_scroll.setObjectName("editScroll")
        edit_scroll.setStyleSheet("#editScroll {background-color: transparent;}")

        self.edit_frame = QWidget()
        self.edit_frame.setObjectName("editFrame")
        self.edit_frame.setStyleSheet(
            """QWidget#editFrame {
            background: transparent;
            }"""
        )

        self.edit_frame_layout = QVBoxLayout(self.edit_frame)
        self.edit_frame.setLayout(self.edit_frame_layout)
        edit_scroll.setWidget(self.edit_frame)

        layout.addWidget(
            SharedRow().expand_button(self.edit_window), 0, 1, Qt.AlignTop | Qt.AlignRight
        )

        return widget

    def build_profile(self, index, lines=None):
        """Add profile into layout."""
        # Clear Layout
        while self.edit_frame_layout.count():
            item = self.edit_frame_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # Build remap and shortcut row instance
        self.shortcut_row_comp = ShortcutRow(self.edit_frame)
        self.default_mode_comp = DefaultMode(self.edit_frame)

        # Add profile widget
        self.middle_stack.setCurrentIndex(0)
        if index == 0:
            shortcut_widget = self.shortcut_row_comp.shortcut_row(self.edit_window, lines)
            self.edit_frame_layout.addWidget(shortcut_widget)

            remap_widget = self.default_mode_comp.remap_row(self.edit_window, lines)
            self.edit_frame_layout.addWidget(remap_widget)

            # Spacer to coupled row tightly
            spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
            self.edit_frame_layout.addItem(spacer)

        elif index == 1:
            if not lines:
                text_mode = self.middle_stack.widget(1)
                text_mode.findChild(QTextEdit).clear()
            self.middle_stack.setCurrentIndex(1)
        else:
            diff.pro_mode(index, lines, self)

    def save_changes(self, mode, top_widget: QWidget):
        """Write script."""
        script_name_entry = top_widget.findChild(QLineEdit, "ScriptNameEntry")
        script_name = script_name_entry.text().strip() + ".ahk"

        if not script_name_entry.text():
            QMessageBox.warning(
                QApplication.activeWindow(), "Input Error", "Please enter a Profile name."
            )
            return

        # Make sure shortcut valid
        write_script = WriteScript(self.middle_stack.widget(0), self.shortcut_row_comp)
        if not write_script.check_shortcut_integrity():
            return

        try:
            output_path = os.path.join(self.main_core.script_dir, script_name)
            with open(output_path, "w", encoding="utf-8") as file:
                condition_string = write_script.write_condition(self.middle_stack.widget(2))

                if mode == "default mode":
                    write_default = WriteDefault(write_script)
                    default_mode = write_default.handle_default_mode(
                        file, condition_string, self.middle_stack
                    )
                    if not default_mode:
                        return
                # Check if pro version mode
                elif diff.pro_write(file, mode, condition_string, self.middle_stack):
                    pass
                else:
                    write_script.handle_text_mode(file, self.middle_stack, condition_string)

        except FileNotFoundError as error:
            print(f"Error: {error}")

        # Update profile list
        self.main_core.update_script_signal.emit()

        # Exit edit window
        self.edit_window.destroy()
