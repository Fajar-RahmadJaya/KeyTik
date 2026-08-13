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
from keytik.utility import constant, diff
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

        # Top part of profile manager
        # top_widget = self.edit_top(script_name, lines)
        # top_widget.setObjectName("TopWidget")
        # edit_layout.addWidget(top_widget, 0, 0, 1, 4)

        # Middle part of profile manager
        self.middle_stack = QStackedWidget()

        self.middle_stack.addWidget(self.scroll_area())

        text_block = TextMode().text_mode_widget(self.edit_window, self.edit_frame, lines)
        self.middle_stack.addWidget(text_block)

        self.middle_stack.addWidget(self.edit_top(script_name, lines))
        edit_layout.addWidget(self.middle_stack)

        # Add profile mode widget
        index = diff.mode_map.get(lines[0].strip().lower())
        self.build_profile(index, lines=lines)

        # Bottom part of profile manager
        # bottom_widget = self.edit_bottom(first_line, top_widget)
        # bottom_widget.setObjectName("BottomWidget")
        # edit_layout.addWidget(bottom_widget, 2, 0, 1, 4)

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

    def primary_command(self, combobox):
        """Command bar primary command."""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget.setLayout(layout)

        setting_button = self.app_bar_icon(code_glyph="\ue713", button_text="Profile Setting")
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

        save_button = self.app_bar_icon(code_glyph="\ue74e", button_text="Save Profile")

        save_button.clicked.connect(
            lambda: self.save_changes(
                combobox.currentText().strip().lower(), self.middle_stack.widget(2)
            )
        )
        layout.addWidget(save_button)

        return widget

    def app_bar_icon(self, code_glyph: str, button_text: str):
        """Button  inspired by WinUI3."""
        button = QPushButton()
        button.setFlat(True)
        button.setStyleSheet("background-color: transparent;")

        layout = QHBoxLayout(button)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        fluent_font = QFont("Segoe Fluent Icons", 12)

        icon = QLabel()
        icon.setFont(fluent_font)
        icon.setText(code_glyph)
        layout.addWidget(icon)

        text = QLabel()
        text.setText(button_text)
        layout.addWidget(text)

        button.setMinimumSize(layout.sizeHint())

        return button

    def edit_top(self, script_name, lines):
        """Top part of profile manager."""
        parse_script = ParseScript()  # Composition

        top_widget = QWidget(self.edit_window)
        top_layout = QGridLayout(top_widget)
        top_layout.setContentsMargins(40, 0, 40, 5)

        script_name_label = QLabel("Profile Name", top_widget)
        script_name_label.setFixedWidth(90)
        top_layout.addWidget(script_name_label, 0, 0, 1, 1)

        script_name_entry = QLineEdit(top_widget)
        script_name_entry.setObjectName("ScriptNameEntry")
        if script_name:
            script_name_entry.setText(script_name.replace(".ahk", ""))
            script_name_entry.setReadOnly(True)
        else:
            script_name_entry.setText("")
            script_name_entry.setReadOnly(False)
        top_layout.addWidget(script_name_entry, 0, 1, 1, 3)

        # Select program to bind
        self.select_program_widget(top_widget, top_layout, lines, parse_script)

        # Select keyboard/mouse to bind
        self.select_device_widget(top_widget, top_layout, lines, parse_script)

        return top_widget

    def select_program_widget(self, top_widget, top_layout, lines, parse_script):
        """Program binding widget."""
        program_label = QLabel("Program", top_widget)
        program_label.setFixedWidth(90)
        top_layout.addWidget(program_label, 1, 0, 1, 1)

        program_entry = QLineEdit(top_widget)
        program_entry.setObjectName("ProgramEntry")
        program_line = parse_script.parse_program(lines) if lines else None
        program_entry.setText(program_line)
        top_layout.addWidget(program_entry, 1, 1, 1, 2)

        program_select_button = QPushButton("Select Program", top_widget)
        program_select_button.setToolTip("Choose program and bind profile to it")
        program_select_button.clicked.connect(
            lambda: SelectProgramUI().program_window(program_entry, self.edit_window)
        )
        program_select_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        top_layout.addWidget(program_select_button, 1, 3, 1, 1)

    def select_device_widget(self, top_widget, top_layout, lines, parse_script):
        """Device binding widget."""
        keyboard_label = QLabel("Device ID", top_widget)
        keyboard_label.setFixedWidth(90)
        top_layout.addWidget(keyboard_label, 2, 0, 1, 1)

        keyboard_entry = QLineEdit(top_widget)
        keyboard_entry.setObjectName("KeyboardEntry")
        device_line = parse_script.parse_device(lines) if lines else None
        keyboard_entry.setText(device_line)
        top_layout.addWidget(keyboard_entry, 2, 1, 1, 2)

        keyboard_select_button = QPushButton("Select Device", top_widget)
        keyboard_select_button.setToolTip("Choose device and bind profile to it")
        keyboard_select_button.clicked.connect(
            lambda: SelectDevice().open_device_selection(self.edit_window, keyboard_entry)
        )
        keyboard_select_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        top_layout.addWidget(keyboard_select_button, 2, 3, 1, 1)

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
                condition_string = write_script.write_condition(top_widget)

                if mode == "default mode":
                    write_default = WriteDefault(write_script)
                    default_mode = write_default.handle_default_mode(file, condition_string)
                    if not default_mode:
                        return
                # Check if pro version mode
                elif diff.pro_write(file, mode, condition_string):
                    pass
                else:
                    text_mode = self.middle_stack.widget(1)
                    write_script.handle_text_mode(
                        file, text_mode.findChild(QTextEdit), condition_string
                    )

        except FileNotFoundError as error:
            print(f"Error: {error}")

        # Update profile list
        self.main_core.update_script_signal.emit()

        # Exit edit window
        self.edit_window.destroy()
