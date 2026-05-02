"UI for create/edit profile"

import os
import traceback
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QWidget, QDialog, QLabel, QLineEdit, QPushButton, QScrollArea,
    QComboBox, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611

from utility import constant
from utility.diff import (mode_item, mode_map)
from utility import utils
from utility import style
from select_program.select_program_ui import SelectProgramUI
from select_device.select_device import SelectDevice
from script_profile.remap_row import RemapRow
from script_profile.write_script import WriteScript
from script_profile.parse_script import ParseScript


class ProfileUI():
    "Create/edit profile UI"
    def __init__(self, main_core):
        # Parameter
        self.main_core = main_core

        # UI
        self.script_name_entry = None
        self.program_entry = None
        self.keyboard_entry = None
        self.edit_window = None

    def edit_script(self, script_name, parent):
        "Create/edit profile window"
        # Handle create new profile
        is_new_profile = not script_name
        if is_new_profile:
            script_path = None
            lines = ["; default\n"]
        else:
            script_path = os.path.join(self.main_core.script_dir, script_name)
            with open(script_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                first_line = file.readline().strip()
            if not lines:
                return

        first_line = lines[0].strip()

        # Edit window
        self.edit_window = QDialog(parent)
        if is_new_profile:
            self.edit_window.setWindowTitle("Create New Profile")
        else:
            self.edit_window.setWindowTitle("Edit Profile")
        self.edit_window.setWindowIcon(QIcon(constant.icon_path))
        geometry = utils.get_geometry(parent, 640, 480)
        self.edit_window.setGeometry(geometry)

        # Composition
        remap_row_comp = RemapRow()
        shortcut_row_comp = remap_row_comp.shortcut_row_comp
        key_listening = remap_row_comp.key_listening_comp

        edit_layout = QGridLayout(self.edit_window)
        edit_layout.setContentsMargins(30, 10, 30, 10)

        # Clear row
        key_listening.copas_rows.clear()
        remap_row_comp.key_rows.clear()
        shortcut_row_comp.shortcut_rows.clear()
        shortcut_row_comp.is_text_mode = False

        # Top part of profile manager
        self.edit_top(script_name, lines, edit_layout, remap_row_comp)

        # Middle part of profile manager
        self.edit_middle(lines, first_line, edit_layout, remap_row_comp)

        # Bottom part of profile manager
        self.edit_bottom(first_line, edit_layout, remap_row_comp)

        self.edit_window.setLayout(edit_layout)
        self.edit_window.exec()

    def edit_top(self, script_name, lines, edit_layout, remap_row_comp):
        "Top part of profile manager"
        parse_script = ParseScript()  # Composition

        top_widget = QWidget(self.edit_window)
        top_layout = QGridLayout(top_widget)
        top_layout.setContentsMargins(40, 0, 40, 5)

        script_name_label = QLabel("Profile Name", top_widget)
        script_name_label.setFixedWidth(90)
        top_layout.addWidget(script_name_label, 0, 0, 1, 1)

        self.script_name_entry = QLineEdit(top_widget)
        if script_name:
            self.script_name_entry.setText(script_name.replace('.ahk', ''))
            self.script_name_entry.setReadOnly(True)
        else:
            self.script_name_entry.setText("")
            self.script_name_entry.setReadOnly(False)
        remap_row_comp.entries_to_disable.append((self.script_name_entry, None))
        top_layout.addWidget(self.script_name_entry, 0, 1, 1, 3)

        program_label = QLabel("Program", top_widget)
        program_label.setFixedWidth(90)
        top_layout.addWidget(program_label, 1, 0, 1, 1)

        self.program_entry = QLineEdit(top_widget)
        if parse_script.parse_program(lines):
            self.program_entry.setText(parse_script.parse_program(lines))
        remap_row_comp.entries_to_disable.append((self.program_entry, None))
        top_layout.addWidget(self.program_entry, 1, 1, 1, 2)

        # Select program to bind
        select_program_ui = SelectProgramUI()  # Composition
        program_select_button = QPushButton("Select Program", top_widget)
        program_select_button.setToolTip("Choose program and bind profile to it")
        program_select_button.clicked.connect(
            lambda: select_program_ui.program_window(self.program_entry, self.edit_window))
        top_layout.addWidget(program_select_button, 1, 3, 1, 1)

        keyboard_label = QLabel("Device ID", top_widget)
        keyboard_label.setFixedWidth(90)
        top_layout.addWidget(keyboard_label, 2, 0, 1, 1)

        self.keyboard_entry = QLineEdit(top_widget)
        if parse_script.parse_device(lines):
            self.keyboard_entry.setText(parse_script.parse_device(lines))
        remap_row_comp.entries_to_disable.append((self.keyboard_entry, None))
        top_layout.addWidget(self.keyboard_entry, 2, 1, 1, 2)

        # Select keyboard/mouse to bind
        select_device = SelectDevice()  # Composition
        keyboard_select_button = QPushButton("Select Device", top_widget)
        keyboard_select_button.setToolTip("Choose device and bind profile to it")
        keyboard_select_button.clicked.connect(
            lambda: select_device.open_device_selection(
                self.edit_window, self.keyboard_entry))
        top_layout.addWidget(keyboard_select_button, 2, 3, 1, 1)

        edit_layout.addWidget(top_widget, 0, 0, 1, 4)

    def edit_middle(self, lines, first_line, edit_layout, remap_row_comp):
        "Middle part of profile manager"
        edit_scroll = QScrollArea(self.edit_window)
        edit_scroll.setWidgetResizable(True)
        edit_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        edit_scroll.setObjectName("editScroll")
        edit_scroll.setStyleSheet(style.scroll_area_style("editScroll"))

        edit_frame = remap_row_comp.handle_parser(lines, first_line, self.edit_window)
        edit_scroll.setWidget(edit_frame)

        edit_layout.addWidget(edit_scroll, 1, 0, 1, 4)

    def edit_bottom(self, first_line, edit_layout, remap_row_comp):
        "Bottom part of profile manager"
        bottom_widget = QWidget(self.edit_window)
        bottom_layout = QGridLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        bottom_layout.setHorizontalSpacing(225)

        save_button = QPushButton("Save Changes", self.edit_window)
        save_button.clicked.connect(
            lambda: self.save_changes(mode_combobox, self.keyboard_entry,
                                      self.program_entry, remap_row_comp))
        save_button.setFixedHeight(28)
        bottom_layout.addWidget(save_button, 0, 0, 1, 1)

        mode_combobox = QComboBox(self.edit_window)
        mode_combobox.addItems(mode_item)
        mode_combobox.setEditable(True)
        mode_combobox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_combobox.lineEdit().setReadOnly(True)
        mode_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        mode_combobox.currentIndexChanged.connect(
            lambda index: remap_row_comp.handle_mode_changed(index, self.edit_window))
        default_index = mode_map.get(first_line.lower(), 0)
        mode_combobox.setCurrentIndex(default_index)
        mode_combobox.setFixedHeight(28)
        bottom_layout.addWidget(mode_combobox, 0, 3, 1, 1)

        edit_layout.addWidget(bottom_widget, 2, 0, 1, 4)

    def save_changes(self, mode_combobox, keyboard_entry, program_entry, remap_row_comp):
        "Write script"
        write_script = WriteScript(remap_row_comp)
        script_name = self.get_script_name()
        if not script_name:
            return

        if not write_script.check_key_integrity():
            return

        try:
            mode = mode_combobox.currentText().strip().lower()
            write_script.handle_write(script_name, mode, keyboard_entry, program_entry)
            self.main_core.update_script_signal.emit()
            self.edit_window.destroy()

        except ValueError as e:
            print(f"Error writing script: {e}")
            traceback.print_exc()

    def get_script_name(self):
        "Get profile name from entry"
        script_name = self.script_name_entry.text().strip()
        if not script_name:
            QMessageBox.warning(None, "Input Error", "Please enter a Profile name.")
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name
