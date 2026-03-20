import os
from PySide6.QtWidgets import (
    QWidget, QDialog, QLabel, QLineEdit, QPushButton, QScrollArea,
    QVBoxLayout, QSpacerItem, QSizePolicy, QComboBox, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

import utility.constant as constant
from utility.diff import (Diff, mode_item, mode_map)

from select_program.select_program_ui import SelectProgramUI

from edit_profile.select_device import SelectDevice
from edit_profile.remap_row import RemapRow
from edit_profile.edit_profile_logic import EditProfileLogic
from select_key.select_key_ui import SelectKeyUI


class EditProfileMain(Diff, RemapRow, SelectProgramUI, SelectDevice,
                      EditProfileLogic, SelectKeyUI):
    def edit_script(self, script_name):
        self.shortcut_row_widgets = []
        self.mapping_row_widgets = []
        self.copas_rows = []

        self.is_text_mode = False

        is_new_profile = not script_name
        if is_new_profile:
            script_path = None
            lines = ["; default\n"]
        else:
            script_path = os.path.join(self.SCRIPT_DIR, script_name)
            with open(script_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                first_line = file.readline().strip()
            if not lines:
                return

        first_line = lines[0].strip()

        self.edit_window = QDialog(self)
        if is_new_profile:
            self.edit_window.setWindowTitle("Create New Profile")
        else:
            self.edit_window.setWindowTitle("Edit Profile")
        self.edit_window.setWindowIcon(QIcon(constant.icon_path))
        self.edit_window.setFixedSize(600, 460)

        edit_layout = QGridLayout(self.edit_window)
        edit_layout.setContentsMargins(30, 10, 30, 10)

        top_widget = QWidget(self.edit_window)
        top_layout = QGridLayout(top_widget)
        top_layout.setContentsMargins(40, 0, 40, 5)

        script_name_label = QLabel("Profile Name", top_widget)
        script_name_label.setFixedWidth(90)
        script_name_entry = QLineEdit(top_widget)
        if script_name:
            script_name_without_extension = script_name.replace('.ahk', '')
            script_name_entry.setText(script_name_without_extension)
            script_name_entry.setReadOnly(True)
        else:
            script_name_entry.setText("")
            script_name_entry.setReadOnly(False)
        self.script_name_entry = script_name_entry
        top_layout.addWidget(script_name_label, 0, 0, 1, 1)
        top_layout.addWidget(script_name_entry, 0, 1, 1, 3)

        program_label = QLabel("Program", top_widget)
        program_label.setFixedWidth(90)
        program_entry = QLineEdit(top_widget)
        program_select_button = QPushButton("Select Program", top_widget)
        program_select_button.setToolTip("Choose program and bind profile to it") # noqa
        program_select_button.clicked.connect(lambda: self.program_window(
            self.program_entry))
        self.program_entry = program_entry
        top_layout.addWidget(program_label, 1, 0, 1, 1)
        top_layout.addWidget(program_entry, 1, 1, 1, 2)
        top_layout.addWidget(program_select_button, 1, 3, 1, 1)

        keyboard_label = QLabel("Device ID", top_widget)
        keyboard_label.setFixedWidth(90)
        keyboard_entry = QLineEdit(top_widget)
        keyboard_select_button = QPushButton("Select Device", top_widget)
        keyboard_select_button.setToolTip("Choose device and bind profile to it") # noqa
        keyboard_select_button.clicked.connect(self.open_device_selection)
        self.keyboard_entry = keyboard_entry
        top_layout.addWidget(keyboard_label, 2, 0, 1, 1)
        top_layout.addWidget(keyboard_entry, 2, 1, 1, 2)
        top_layout.addWidget(keyboard_select_button, 2, 3, 1, 1)

        device_id = self.parse_device(lines)
        if device_id:
            keyboard_entry.setText(device_id)

        program_entry_value = self.parse_program(lines)
        if program_entry_value:
            program_entry.setText(program_entry_value)

        edit_layout.addWidget(top_widget, 0, 0, 1, 4)

        self.edit_scroll = QScrollArea(self.edit_window)
        self.edit_scroll.setFixedSize(535, 305)
        self.edit_scroll.setWidgetResizable(True)
        self.edit_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        edit_layout.addWidget(self.edit_scroll, 1, 0, 1, 4)

        self.edit_frame = QWidget()
        self.edit_scroll.setWidget(self.edit_frame)

        self.edit_frame_layout = QVBoxLayout(self.edit_frame)
        self.edit_frame.setLayout(self.edit_frame_layout)

        self.key_rows = []
        self.shortcut_rows = []

        self.handle_parser(lines, first_line)

        self.edit_frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum,
                                                   QSizePolicy.Expanding))

        bottom_widget = QWidget(self.edit_window)
        bottom_layout = QGridLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        bottom_layout.setHorizontalSpacing(225)

        save_button = QPushButton("Save Changes", self.edit_window)
        save_button.clicked.connect(lambda: self.save_changes(script_name))
        bottom_layout.addWidget(save_button, 0, 0, 1, 1)

        mode_combobox = QComboBox(self.edit_window)
        mode_combobox.addItems(mode_item)
        mode_combobox.setEditable(True)
        mode_combobox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_combobox.lineEdit().setReadOnly(True)
        mode_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mode_combobox = mode_combobox
        bottom_layout.addWidget(mode_combobox, 0, 3, 1, 1)

        edit_layout.addWidget(bottom_widget, 2, 0, 1, 4)

        first_line_lower = first_line.lower()

        default_index = mode_map.get(first_line_lower, 0)
        mode_combobox.setCurrentIndex(default_index)

        on_mode_changed = self.handle_mode_changed
        mode_combobox.currentIndexChanged.connect(on_mode_changed)

        self.edit_window.setLayout(edit_layout)
        self.edit_window.exec()
