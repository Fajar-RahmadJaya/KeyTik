"UI for create/edit profile"

import os
import traceback
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QWidget, QDialog, QLabel, QLineEdit, QPushButton, QScrollArea,
    QComboBox, QGridLayout, QMessageBox, QVBoxLayout, QSpacerItem,
    QSizePolicy
)
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611

from utility import constant
from utility.diff import diff_comp
from utility import style
from select_program.select_program_ui import SelectProgramUI
from select_device.select_device import SelectDevice
from script_profile.remap_row import RemapRow
from script_profile.remap_row_core import RemapRowCore
from script_profile.write_script import WriteScript
from script_profile.parse_script import ParseScript


class ProfileUI():
    "Create/edit profile UI"
    def __init__(self, main_core):
        # Parameter
        self.main_core = main_core

        # Composition
        # Used for save change since it need for
        # current remap row composition (Mode changed or edit middle)
        self.remap_row_comp = None

        # UI
        self.edit_window = None
        self.edit_frame = QWidget()
        self.edit_frame_layout = QVBoxLayout(self.edit_frame)

    def edit_script(self, script_name, parent):
        "Create/edit profile window"
        self.edit_window = QDialog(parent)
        # Handle Create New Profile
        if not script_name:
            script_path = None
            lines = ["; default\n"]

            self.edit_window.setWindowTitle("Create New Profile")
        # Handle Edit Profile
        else:
            script_path = os.path.join(self.main_core.script_dir, script_name)
            with open(script_path, 'r', encoding='utf-8') as file:
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
        top_widget, entries_to_disable = self.edit_top(script_name, lines)
        edit_layout.addWidget(top_widget, 0, 0, 1, 4)

        # Middle part of profile manager
        edit_scroll = self.edit_middle(lines, entries_to_disable)
        edit_layout.addWidget(edit_scroll, 1, 0, 1, 4)

        # Bottom part of profile manager
        bottom_widget = self.edit_bottom(first_line, entries_to_disable)
        edit_layout.addWidget(bottom_widget, 2, 0, 1, 4)

        self.edit_window.setLayout(edit_layout)
        self.edit_window.exec()

    def edit_top(self, script_name, lines):
        "Top part of profile manager"
        parse_script = ParseScript()  # Composition

        entries_to_disable =  []  # Used for remap row

        top_widget = QWidget(self.edit_window)
        top_layout = QGridLayout(top_widget)
        top_layout.setContentsMargins(40, 0, 40, 5)

        script_name_label = QLabel("Profile Name", top_widget)
        script_name_label.setFixedWidth(90)
        top_layout.addWidget(script_name_label, 0, 0, 1, 1)

        script_name_entry = QLineEdit(top_widget)
        if script_name:
            script_name_entry.setText(script_name.replace('.ahk', ''))
            script_name_entry.setReadOnly(True)
        else:
            script_name_entry.setText("")
            script_name_entry.setReadOnly(False)
        entries_to_disable.append((script_name_entry, None))
        top_layout.addWidget(script_name_entry, 0, 1, 1, 3)

        # Select program to bind
        program_label = QLabel("Program", top_widget)
        program_label.setFixedWidth(90)
        top_layout.addWidget(program_label, 1, 0, 1, 1)

        program_entry = QLineEdit(top_widget)
        if parse_script.parse_program(lines):
            program_entry.setText(parse_script.parse_program(lines))
        entries_to_disable.append((program_entry, None))
        top_layout.addWidget(program_entry, 1, 1, 1, 2)

        program_select_button = QPushButton("Select Program", top_widget)
        program_select_button.setToolTip("Choose program and bind profile to it")
        program_select_button.clicked.connect(
            lambda: SelectProgramUI().program_window(program_entry, self.edit_window))
        top_layout.addWidget(program_select_button, 1, 3, 1, 1)

        # Select keyboard/mouse to bind
        keyboard_label = QLabel("Device ID", top_widget)
        keyboard_label.setFixedWidth(90)
        top_layout.addWidget(keyboard_label, 2, 0, 1, 1)

        keyboard_entry = QLineEdit(top_widget)
        if parse_script.parse_device(lines):
            keyboard_entry.setText(parse_script.parse_device(lines))
        entries_to_disable.append((keyboard_entry, None))
        top_layout.addWidget(keyboard_entry, 2, 1, 1, 2)

        keyboard_select_button = QPushButton("Select Device", top_widget)
        keyboard_select_button.setToolTip("Choose device and bind profile to it")
        keyboard_select_button.clicked.connect(
            lambda: SelectDevice().open_device_selection(
                self.edit_window, keyboard_entry))
        top_layout.addWidget(keyboard_select_button, 2, 3, 1, 1)

        return top_widget, entries_to_disable

    def edit_middle(self, lines, entries_to_disable):
        "Middle part of profile manager"

        edit_scroll = QScrollArea(self.edit_window)
        edit_scroll.setWidgetResizable(True)
        edit_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        edit_scroll.setObjectName("editScroll")
        edit_scroll.setStyleSheet("#editScroll {background-color: transparent;}")

        self.remap_row_comp = RemapRowCore()
        key_map = self.remap_row_comp.load_key_list()
        mode_line = lines[0].strip() if lines else "; default"

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
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add profile mode widget
        self.remap_row_comp = RemapRow(self.edit_frame, self.edit_frame_layout, entries_to_disable)

        # Default mode
        if mode_line == "; default":
            self.remap_row_comp.default_mode_widget(lines, key_map, self.edit_window)

        elif mode_line == "; text":
            self.remap_row_comp.shortcut_row_comp.text_mode_widget(lines, key_map, self.edit_window)

        else:
            diff_comp.pro_parser(lines, self.remap_row_comp.shortcut_row_comp, self.edit_window)
            self.edit_frame_layout.addItem(spacer)

        edit_scroll.setWidget(self.edit_frame)

        return edit_scroll

    def edit_bottom(self, first_line, entries_to_disable):
        "Bottom part of profile manager"
        bottom_widget = QWidget(self.edit_window)
        bottom_layout = QGridLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        bottom_layout.setHorizontalSpacing(225)

        save_button = QPushButton("Save Changes", self.edit_window)
        save_button.clicked.connect(
            lambda: self.save_changes(mode_combobox, entries_to_disable))
        save_button.setFixedHeight(28)
        bottom_layout.addWidget(save_button, 0, 0, 1, 1)

        mode_combobox = QComboBox(self.edit_window)
        mode_combobox.addItems(diff_comp.mode_item)
        mode_combobox.setEditable(True)
        mode_combobox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_combobox.lineEdit().setReadOnly(True)
        mode_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        default_index = diff_comp.mode_map.get(first_line.lower(), 0)
        mode_combobox.setCurrentIndex(default_index)

        mode_combobox.currentIndexChanged.connect(
            lambda index: self.handle_mode_changed(index, self.edit_window, entries_to_disable))

        mode_combobox.setFixedHeight(28)
        bottom_layout.addWidget(mode_combobox, 0, 3, 1, 1)

        return bottom_widget

    def handle_mode_changed(self, index, parent_window, entries_to_disable):
        "Action when mode changed from combobox (can be moved)"
        # Clear Layout
        while self.edit_frame_layout.count():
            item = self.edit_frame_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # Spacer to coupled row tightly
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        # Add profile widget
        self.remap_row_comp = RemapRow(self.edit_frame, self.edit_frame_layout, entries_to_disable)
        shortcut_row_comp = self.remap_row_comp.shortcut_row_comp
        if index == 0:
            shortcut_row_comp.is_text_mode = False
            shortcut_row_comp.shortcut_title()
            shortcut_row_comp.shortcut_row(parent_window)
            remap_title_widget = self.remap_row_comp.remap_title()
            self.edit_frame_layout.addWidget(remap_title_widget)
            self.remap_row_comp.remap_row(parent_window=parent_window)
            self.edit_frame_layout.addItem(spacer)

        elif index == 1:
            shortcut_row_comp.is_text_mode = True
            shortcut_row_comp.shortcut_title()
            shortcut_row_comp.shortcut_row(parent_window)
            self.edit_frame_layout.addItem(spacer)

        else:
            diff_comp.pro_mode(index, shortcut_row_comp, parent_window)
            self.edit_frame_layout.addItem(spacer)

    def save_changes(self, mode_combobox, entries_to_disable):
        "Write script"
        write_script = WriteScript(self.remap_row_comp)
        script_name = self.get_script_name(entries_to_disable[0])
        if not script_name:
            return

        if not write_script.check_key_integrity():
            return

        try:
            mode = mode_combobox.currentText().strip().lower()
            write_script.handle_write(
                script_name, mode,
                program_entry=entries_to_disable[1],
                keyboard_entry=entries_to_disable[2])
            self.main_core.update_script_signal.emit()
            self.edit_window.destroy()

        except ValueError as e:
            print(f"Error writing script: {e}")
            traceback.print_exc()

    def get_script_name(self, script_name_entry):
        "Get profile name from entry"
        script_name = script_name_entry.text().strip()
        if not script_name:
            QMessageBox.warning(None, "Input Error", "Please enter a Profile name.")
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name
