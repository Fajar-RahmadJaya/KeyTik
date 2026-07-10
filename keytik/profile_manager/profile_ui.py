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
from PySide6.QtGui import QIcon  # pylint: disable=E0611
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QApplication,
    QComboBox,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from keytik.profile_manager.parse_script import ParseScript
from keytik.profile_manager.write_script import WriteDefault, WriteScript
from keytik.profile_mode.default_mode import DefaultMode
from keytik.profile_mode.shortcut_row import ShortcutRow
from keytik.profile_mode.text_mode import TextMode
from keytik.select_device.select_device import SelectDevice
from keytik.select_program.select_program_ui import SelectProgramUI
from keytik.utility import constant, diff, style


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

    def edit_script(self, script_name, parent):
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

            self.edit_window.setWindowTitle("Edit Profile")

        first_line = lines[0].strip()

        self.edit_window.setWindowIcon(QIcon(constant.icon_path))
        geometry = style.get_geometry(parent, 640, 480)
        self.edit_window.setGeometry(geometry)
        style.apply_mica(self.edit_window)

        edit_layout = QGridLayout(self.edit_window)
        edit_layout.setContentsMargins(30, 10, 30, 10)

        # Top part of profile manager
        top_widget = self.edit_top(script_name, lines)
        edit_layout.addWidget(top_widget, 0, 0, 1, 4)

        # Middle part of profile manager
        edit_scroll = self.edit_middle(lines)
        edit_layout.addWidget(edit_scroll, 1, 0, 1, 4)

        # Bottom part of profile manager
        bottom_widget = self.edit_bottom(first_line, top_widget)
        edit_layout.addWidget(bottom_widget, 2, 0, 1, 4)

        self.edit_window.setLayout(edit_layout)
        self.edit_window.exec()

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

    def edit_middle(self, lines):
        """Middle part of profile manager."""
        edit_scroll = QScrollArea(self.edit_window)
        edit_scroll.setWidgetResizable(True)
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

        # Spacer to coupled row tightly
        # spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add profile mode widget
        index = diff.mode_map.get(lines[0].strip().lower())
        self.build_profile(index, lines=lines)

        edit_scroll.setWidget(self.edit_frame)

        return edit_scroll

    def build_profile(self, index, lines=None):
        """Add profile into layout."""
        # Clear Layout
        while self.edit_frame_layout.count():
            item = self.edit_frame_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # Spacer to coupled row tightly
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Build remap and shortcut row instance
        self.shortcut_row_comp = ShortcutRow(self.edit_frame)
        self.default_mode_comp = DefaultMode(self.edit_frame)

        # Add profile widget
        if index == 0:
            self.default_mode_widget(self.edit_window, lines)

        elif index == 1:
            text_block = TextMode().text_block(lines)
            self.edit_frame_layout.addWidget(text_block)

        else:
            diff.pro_mode(index, lines, self)
            self.edit_frame_layout.addItem(spacer)

    def default_mode_widget(self, parent_window, lines=None):
        """Default mode frame."""
        parse_script = ParseScript()  # Composition

        parsed_shortcuts_list = parse_script.parse_shortcuts(lines) if lines else None
        shortcut_widget = self.shortcut_row_comp.shortcut_row(parent_window, parsed_shortcuts_list)
        self.edit_frame_layout.addWidget(shortcut_widget)

        parsed_remap_list = parse_script.parse_default_mode(lines) if lines else None
        remap_widget = self.default_mode_comp.remap_row(parent_window, parsed_remap_list)
        self.edit_frame_layout.addWidget(remap_widget)

    def edit_bottom(self, first_line, top_widget):
        """Bottom part of profile manager."""
        bottom_widget = QWidget(self.edit_window)
        bottom_layout = QGridLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        bottom_layout.setHorizontalSpacing(225)

        save_button = QPushButton("Save Changes", self.edit_window)
        save_button.clicked.connect(
            lambda: self.save_changes(mode_combobox.currentText().strip().lower(), top_widget)
        )
        save_button.setFixedHeight(28)
        save_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        bottom_layout.addWidget(save_button, 0, 0, 1, 1)

        mode_combobox = QComboBox(self.edit_window)
        mode_combobox.addItems(diff.mode_item)
        mode_combobox.setEditable(True)
        mode_combobox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_combobox.lineEdit().setReadOnly(True)
        mode_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        default_index = diff.mode_map.get(first_line.lower(), 0)
        mode_combobox.setCurrentIndex(default_index)
        mode_combobox.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        mode_combobox.currentIndexChanged.connect(self.build_profile)

        mode_combobox.setFixedHeight(28)
        bottom_layout.addWidget(mode_combobox, 0, 3, 1, 1)

        return bottom_widget

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
        write_script = WriteScript(self.default_mode_comp, self.shortcut_row_comp)
        if not write_script.check_shortcut_integrity():
            return

        try:
            output_path = os.path.join(self.main_core.script_dir, script_name)
            with open(output_path, "w", encoding="utf-8") as file:
                condition_string = write_script.write_condition(top_widget)

                if mode == "text mode":
                    write_script.handle_text_mode(file, self.edit_frame, condition_string)
                elif mode == "default mode":
                    write_default = WriteDefault(write_script)
                    write_default.handle_default_mode(file, condition_string)
                else:
                    diff.pro_write(file, mode, condition_string)

        except FileNotFoundError as error:
            print(f"Error: {error}")

        # Update profile list
        self.main_core.update_script_signal.emit()

        # Exit edit window
        self.edit_window.destroy()
