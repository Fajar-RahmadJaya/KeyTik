"UI for create/edit profile"

import os
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QWidget,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QComboBox,
    QGridLayout,
    QMessageBox,
    QVBoxLayout,
    QSpacerItem,
    QSizePolicy,
    QTextEdit,
)
from PySide6.QtCore import Qt  # pylint: disable=E0611
from PySide6.QtGui import QIcon  # pylint: disable=E0611

from utility import constant
from utility.diff import diff_comp
from utility import style
from select_program.select_program_ui import SelectProgramUI
from select_device.select_device import SelectDevice
from script_profile.remap_row import RemapRow, ShortcutRow
from script_profile.write_script import WriteScript, WriteDefault
from script_profile.parse_script import ParseScript


class ProfileUI:
    "Create/edit profile UI"

    def __init__(self, main_core):
        # Parameter
        self.main_core = main_core

        # Composition
        # Used for save change since it need for
        # current remap row composition (Mode changed or edit middle)
        self.remap_row_comp = None
        self.shortcut_row_comp = None

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
            with open(script_path, "r", encoding="utf-8") as file:
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
        "Top part of profile manager"
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
        "Program binding widget"
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
        top_layout.addWidget(program_select_button, 1, 3, 1, 1)

    def select_device_widget(self, top_widget, top_layout, lines, parse_script):
        "Device binding widget"
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
            lambda: SelectDevice().open_device_selection(
                self.edit_window, keyboard_entry
            )
        )
        top_layout.addWidget(keyboard_select_button, 2, 3, 1, 1)

    def edit_middle(self, lines):
        "Middle part of profile manager"

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
        index = diff_comp.mode_map.get(lines[0].strip().lower())
        self.build_profile(index, lines=lines)

        edit_scroll.setWidget(self.edit_frame)

        return edit_scroll

    def build_profile(self, index, lines=None):
        "Add profile into layout"
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
        self.remap_row_comp = RemapRow(self.edit_frame)

        # Add profile widget
        if index == 0:
            self.default_mode_widget(self.edit_window, lines)

        elif index == 1:
            text_block = self.text_block(lines)
            self.edit_frame_layout.addWidget(text_block)

        else:
            diff_comp.pro_mode(index, lines, self)
            self.edit_frame_layout.addItem(spacer)

    def default_mode_widget(self, parent_window, lines=None):
        "Default mode frame"
        parse_script = ParseScript()  # Composition

        parsed_shortcuts_list = parse_script.parse_shortcuts(lines) if lines else None
        shortcut_widget = self.shortcut_row_comp.shortcut_row(
            parent_window, parsed_shortcuts_list
        )
        self.edit_frame_layout.addWidget(shortcut_widget)

        parsed_remap_list = parse_script.parse_default_mode(lines) if lines else None
        remap_widget = self.remap_row_comp.remap_row(parent_window, parsed_remap_list)
        self.edit_frame_layout.addWidget(remap_widget)

    def text_block(self, lines=None):
        "Text mode frame(to do: fix)"
        text_block = QTextEdit()
        text_block.setLineWrapMode(QTextEdit.WidgetWidth)
        text_block.setFixedHeight(14 * text_block.fontMetrics().height())
        text_block.setFontPointSize(10)
        text_block.setReadOnly(False)
        text_block.setStyleSheet(style.TEXT_BLOCK)
        text_content = self.extract_and_filter_content(lines).strip() if lines else None
        text_block.setPlainText(text_content)

        return text_block

    def extract_and_filter_content(self, lines):
        "Get text block value from the marker"
        inside = False
        result_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped == "; Text mode start":
                inside = True
                continue
            if stripped == "; Text mode end":
                inside = False
                continue
            if inside:
                result_lines.append(line)

        return "".join(result_lines)

    def edit_bottom(self, first_line, top_widget):
        "Bottom part of profile manager"
        bottom_widget = QWidget(self.edit_window)
        bottom_layout = QGridLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 0)
        bottom_layout.setHorizontalSpacing(225)

        save_button = QPushButton("Save Changes", self.edit_window)
        save_button.clicked.connect(
            lambda: self.save_changes(
                mode_combobox.currentText().strip().lower(), top_widget
            )
        )
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

        mode_combobox.currentIndexChanged.connect(self.build_profile)

        mode_combobox.setFixedHeight(28)
        bottom_layout.addWidget(mode_combobox, 0, 3, 1, 1)

        return bottom_widget

    def save_changes(self, mode, top_widget: QWidget):
        "Write script"
        script_name_entry = top_widget.findChild(QLineEdit, "ScriptNameEntry")
        script_name = script_name_entry.text().strip() + ".ahk"

        if not script_name:
            QMessageBox.warning(None, "Input Error", "Please enter a Profile name.")
            return

        try:
            output_path = os.path.join(self.main_core.script_dir, script_name)
            with open(output_path, "w", encoding="utf-8") as file:
                write_script = WriteScript(self.remap_row_comp, self.shortcut_row_comp)
                condition_string = write_script.write_condition(top_widget)

                if mode == "text mode":
                    write_script.handle_text_mode(file, condition_string)
                elif mode == "default mode":
                    write_default = WriteDefault(write_script)
                    write_default.handle_default_mode(file, condition_string)
                else:
                    diff_comp.pro_write(file, mode, condition_string)

        except FileNotFoundError as error:
            print(f"Error: {error}")

        # Update profile list
        self.main_core.update_script_signal.emit()

        # Exit edit window
        self.edit_window.destroy()
