"UI for create/edit profile"

import os
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QWidget, QDialog, QLabel, QLineEdit, QPushButton, QScrollArea,
    QVBoxLayout, QSpacerItem, QSizePolicy, QComboBox, QGridLayout
)
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611

from utility import constant
from utility.diff import (Diff, mode_item, mode_map)
from utility import utils

from select_program.select_program_ui import SelectProgramUI

from select_device.select_device_ui import SelectDeviceUI
from script_profile.remap_row import RemapRow
from script_profile.write_script import WriteScript
from select_key.select_key_ui import SelectKeyUI


class ProfileUI(Diff, RemapRow, SelectProgramUI, SelectDeviceUI,
                SelectKeyUI, WriteScript):
    "Create/edit profile UI"
    def __init__(self):
        super().__init__(self.edit_frame)
        # Variables
        self.copas_rows = []
        self.key_rows = []
        self.shortcut_rows = []
        self.files_opener_rows = []
        self.files_opener_row_widgets = []
        self.is_text_mode = False
        self.script_dir = utils.active_dir

        # UI
        self.script_name_entry = None
        self.program_entry = None
        self.keyboard_entry = None
        self.edit_frame = None

    def edit_script(self, script_name):
        "Create/edit profile window"
        # Clear row
        self.copas_rows = []
        self.key_rows = []
        self.shortcut_rows = []
        self.shortcut_row_widgets = []
        self.mapping_row_widgets = []
        self.is_text_mode = False

        # Handle create new profile
        is_new_profile = not script_name
        if is_new_profile:
            script_path = None
            lines = ["; default\n"]
        else:
            script_path = os.path.join(self.script_dir, script_name)
            with open(script_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                first_line = file.readline().strip()
            if not lines:
                return

        first_line = lines[0].strip()

        # Edit window
        self.edit_window = QDialog(self)
        if is_new_profile:
            self.edit_window.setWindowTitle("Create New Profile")
        else:
            self.edit_window.setWindowTitle("Edit Profile")
        self.edit_window.setWindowIcon(QIcon(constant.icon_path))
        self.edit_window.setFixedSize(600, 460)

        edit_layout = QGridLayout(self.edit_window)
        edit_layout.setContentsMargins(30, 10, 30, 10)

        # Top part of profile manager
        top_widget = self.edit_top(script_name, lines)
        edit_layout.addWidget(top_widget, 0, 0, 1, 4)

        # Middle part of profile manager
        edit_scroll = self.edit_middle(lines, first_line)
        edit_layout.addWidget(edit_scroll, 1, 0, 1, 4)

        # Bottom part of profile manager
        bottom_widget = self.edit_bottom(script_name, first_line)
        edit_layout.addWidget(bottom_widget, 2, 0, 1, 4)

        self.edit_window.setLayout(edit_layout)
        self.edit_window.exec()

    def edit_top(self, script_name, lines):
        "Top part of profile manager"
        top_widget = QWidget(self.edit_window)
        top_layout = QGridLayout(top_widget)
        top_layout.setContentsMargins(40, 0, 40, 5)

        script_name_label = QLabel("Profile Name", top_widget)
        script_name_label.setFixedWidth(90)
        top_layout.addWidget(script_name_label, 0, 0, 1, 1)

        self.script_name_entry = QLineEdit(top_widget)
        if script_name:
            script_name_without_extension = script_name.replace('.ahk', '')
            self.script_name_entry.setText(script_name_without_extension)
            self.script_name_entry.setReadOnly(True)
        else:
            self.script_name_entry.setText("")
            self.script_name_entry.setReadOnly(False)
        top_layout.addWidget(self.script_name_entry, 0, 1, 1, 3)

        program_label = QLabel("Program", top_widget)
        program_label.setFixedWidth(90)
        top_layout.addWidget(program_label, 1, 0, 1, 1)

        self.program_entry = QLineEdit(top_widget)
        program_entry_value = self.parse_program(lines)
        if program_entry_value:
            self.program_entry.setText(program_entry_value)
        top_layout.addWidget(self.program_entry, 1, 1, 1, 2)

        program_select_button = QPushButton("Select Program", top_widget)
        program_select_button.setToolTip("Choose program and bind profile to it")
        program_select_button.clicked.connect(lambda: self.program_window(self.program_entry))
        top_layout.addWidget(program_select_button, 1, 3, 1, 1)

        keyboard_label = QLabel("Device ID", top_widget)
        keyboard_label.setFixedWidth(90)
        top_layout.addWidget(keyboard_label, 2, 0, 1, 1)

        self.keyboard_entry = QLineEdit(top_widget)
        device_id = self.parse_device(lines)
        if device_id:
            self.keyboard_entry.setText(device_id)
        top_layout.addWidget(self.keyboard_entry, 2, 1, 1, 2)

        keyboard_select_button = QPushButton("Select Device", top_widget)
        keyboard_select_button.setToolTip("Choose device and bind profile to it")
        keyboard_select_button.clicked.connect(
            lambda: self.open_device_selection(self.edit_window, self.keyboard_entry))
        top_layout.addWidget(keyboard_select_button, 2, 3, 1, 1)

        return top_widget

    def edit_middle(self, lines, first_line):
        "Middle part of profile manager"
        edit_scroll = QScrollArea(self.edit_window)
        edit_scroll.setFixedSize(535, 305)
        edit_scroll.setWidgetResizable(True)
        edit_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.edit_frame = QWidget()
        edit_scroll.setWidget(self.edit_frame)

        self.edit_frame_layout = QVBoxLayout(self.edit_frame)
        self.edit_frame.setLayout(self.edit_frame_layout)

        self.handle_parser(lines, first_line)

        self.edit_frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum,
                                                    QSizePolicy.Expanding))

        return edit_scroll

    def edit_bottom(self, script_name, first_line):
        "Bottom part of profile manager"
        bottom_widget = QWidget(self.edit_window)
        bottom_layout = QGridLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        bottom_layout.setHorizontalSpacing(225)

        save_button = QPushButton("Save Changes", self.edit_window)
        save_button.clicked.connect(lambda: self.save_changes(script_name, mode_combobox))
        bottom_layout.addWidget(save_button, 0, 0, 1, 1)

        mode_combobox = QComboBox(self.edit_window)
        mode_combobox.addItems(mode_item)
        mode_combobox.setEditable(True)
        mode_combobox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_combobox.lineEdit().setReadOnly(True)
        mode_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        mode_combobox.currentIndexChanged.connect(self.handle_mode_changed)
        default_index = mode_map.get(first_line.lower(), 0)
        mode_combobox.setCurrentIndex(default_index)
        bottom_layout.addWidget(mode_combobox, 0, 3, 1, 1)

        return bottom_widget

    def handle_mode_changed(self, index):
        "Action when mode changed from combobox (can be moved)"
        while self.edit_frame_layout.count():
            item = self.edit_frame_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        self.key_rows = []
        self.shortcut_rows = []
        if hasattr(self, "files_opener_rows"):
            self.files_opener_rows = []
        if hasattr(self, "files_opener_row_widgets"):
            self.files_opener_row_widgets = []
        if hasattr(self, "text_block"):
            self.text_block = None
        self.is_text_mode = False

        if index == 0:
            self.is_text_mode = False
            self.shortcut_title()
            self.shortcut_row()
            self.remap_title()
            self.remap_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40,
                                            QSizePolicy.Minimum,
                                            QSizePolicy.Expanding))

        elif index == 1:
            self.is_text_mode = True
            self.shortcut_title()
            self.shortcut_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40,
                                            QSizePolicy.Minimum,
                                            QSizePolicy.Expanding))

        else:
            self.pro_mode(index)
