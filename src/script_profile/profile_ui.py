"UI for create/edit profile"

import os
import traceback
import re
from PySide6.QtWidgets import (  # pylint: disable=E0611
    QWidget, QDialog, QLabel, QLineEdit, QPushButton, QScrollArea,
    QVBoxLayout, QSpacerItem, QSizePolicy, QComboBox, QGridLayout,
    QMessageBox
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
from script_profile.parse_script import ParseScript
from select_key.select_key_ui import SelectKeyUI
from core.main_core import MainCore


class ProfileUI():
    "Create/edit profile UI"
    def __init__(self):
        # UI
        self.script_name_entry = None
        self.program_entry = None
        self.keyboard_entry = None
        self.edit_frame = None

        # Composition
        self.select_program_ui = SelectProgramUI()
        self.select_device_ui = SelectDeviceUI()
        self.remap_row = RemapRow(self.edit_frame, self.edit_window,
                                  self.script_name_entry, self.keyboard_entry,
                                  self.program_entry)
        self.write_script = WriteScript()
        self.select_key_ui = SelectKeyUI()
        self.main_core = MainCore()
        self.diff = Diff()
        self.parse_script = ParseScript()

        # Variables
        self.copas_rows = []
        self.key_rows = []
        self.shortcut_rows = []
        self.files_opener_rows = []
        self.files_opener_row_widgets = []
        self.is_text_mode = False
        self.script_dir = utils.active_dir

    def edit_script(self, script_name):
        "Create/edit profile window"
        # Clear row
        self.copas_rows = []
        self.key_rows = []
        self.shortcut_rows = []
        self.remap_row.shortcut_row_widgets = []
        self.remap_row.mapping_row_widgets = []
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
        program_entry_value = self.parse_script.parse_program(lines)
        if program_entry_value:
            self.program_entry.setText(program_entry_value)
        top_layout.addWidget(self.program_entry, 1, 1, 1, 2)

        program_select_button = QPushButton("Select Program", top_widget)
        program_select_button.setToolTip("Choose program and bind profile to it")
        program_select_button.clicked.connect(lambda: self.select_program_ui.program_window(self.program_entry))
        top_layout.addWidget(program_select_button, 1, 3, 1, 1)

        keyboard_label = QLabel("Device ID", top_widget)
        keyboard_label.setFixedWidth(90)
        top_layout.addWidget(keyboard_label, 2, 0, 1, 1)

        self.keyboard_entry = QLineEdit(top_widget)
        device_id = self.parse_script.parse_device(lines)
        if device_id:
            self.keyboard_entry.setText(device_id)
        top_layout.addWidget(self.keyboard_entry, 2, 1, 1, 2)

        keyboard_select_button = QPushButton("Select Device", top_widget)
        keyboard_select_button.setToolTip("Choose device and bind profile to it")
        keyboard_select_button.clicked.connect(
            lambda: self.select_device_ui.open_device_selection(self.edit_window, self.keyboard_entry))
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

        self.remap_row.handle_parser(lines, first_line)

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
        mode_combobox.currentIndexChanged.connect(self.remap_row.handle_mode_changed)
        default_index = mode_map.get(first_line.lower(), 0)
        mode_combobox.setCurrentIndex(default_index)
        bottom_layout.addWidget(mode_combobox, 0, 3, 1, 1)

        return bottom_widget

    # ----------------- From write_script -----------------

    def get_script_name(self):
        "Get profile name from entry"
        script_name = self.script_name_entry.text().strip()
        if not script_name:
            QMessageBox.warning(None, "Input Error", "Please enter a Profile name.")
            return None

        if not script_name.endswith('.ahk'):
            script_name += '.ahk'

        return script_name

    def save_changes(self, script_name, mode_combobox):
        "Write script"
        script_name = self.get_script_name()
        if not script_name:
            return

        if not self.check_key_integrity():
            return

        try:
            mode = mode_combobox.currentText().strip().lower()
            self.is_text_mode = mode == "text mode"
            self.handle_write(script_name, mode)
            self.main_core.update_script_signal.emit()
            self.edit_window.destroy()

        except ValueError as e:
            print(f"Error writing script: {e}")
            traceback.print_exc()

    def handle_write(self, script_name, mode):
        "Action when saving profile (Can be moved)"
        output_path = os.path.join(self.script_dir, script_name)
        key_translations = self.write_script.load_key_translations()

        with open(output_path, 'w', encoding='utf-8') as file:
            if mode == "text mode":
                self.handle_text_mode(file)
            elif mode == "default mode":
                self.handle_default_mode(file)
            else:
                self.diff.pro_write(file, mode, key_translations)

    def handle_default_mode(self, file):
        "Write default mode"
        file.write("; default\n")
        self.main_core.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")
        file.write("#Requires AutoHotkey v2.0\n")

        write_hotif = self.write_condition(file,
                                            write_shortcuts=True,
                                            write_program=True,
                                            write_device=True)

        self.write_script.process_key_remaps(file)

        if write_hotif:
            file.write("#HotIf\n")

    def handle_text_mode(self, file):
        "Write text mode"
        file.write("; text\n")
        self.main_core.generate_exit_key(os.path.basename(file.name), file)
        file.write("#SingleInstance force\n")
        file.write("#Requires AutoHotkey v2.0\n")

        write_hotif = self.write_condition(file,
                                            write_shortcuts=True,
                                            write_program=True,
                                            write_device=True)

        text_content = self.remap_row.text_block.toPlainText().strip()
        if text_content:
            file.write("; Text mode start\n")
            file.write(text_content + '\n')
            file.write("; Text mode end\n")

        if write_hotif:
            file.write("#HotIf\n")

    def check_key_integrity(self):
        "Make sure there is no conflict on profile input"
        shortcut_types = {"normal": [], "caps": []}
        caps_on_present = False
        caps_off_present = False
        num_on_present = False
        num_off_present = False
        for shortcut_row in self.shortcut_rows:
            if self.write_script.is_widget_valid(shortcut_row):
                shortcut = shortcut_row[0].text().strip()
                if shortcut:
                    if shortcut.lower() == "capslock on":
                        shortcut_types["caps"].append(shortcut)
                        caps_on_present = True
                    elif shortcut.lower() == "capslock off":
                        shortcut_types["caps"].append(shortcut)
                        caps_off_present = True
                    elif shortcut.lower() == "numlock on":
                        shortcut_types["caps"].append(shortcut)
                        num_on_present = True
                    elif shortcut.lower() == "numlock off":
                        shortcut_types["caps"].append(shortcut)
                        num_off_present = True
                    else:
                        shortcut_types["normal"].append(shortcut)

        if shortcut_types["normal"] and shortcut_types["caps"]:
            msg = (QMessageBox(self.edit_window
                                if hasattr(self, "edit_window")
                                else None))
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use 'CapsLock On' or 'CapsLock Off' "
                        "or 'NumLock On' or 'Numlock Off' together with normal keys as shortcuts. "
                        "Please use only one type "
                        "(either normal keys or CapsLock NumLock ON/OFF) for all shortcuts.")
            msg.setWindowIcon(QIcon(constant.icon_path))
            msg.exec()
            return False
        if caps_on_present and caps_off_present:
            msg = (QMessageBox(self.edit_window
                                if hasattr(self, "edit_window")
                                else None))
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use both 'CapsLock ON' and 'CapsLock OFF' at the same time. "
                        "Please use only one of of them. If you need both, just use 'Caps Lock'.")
            msg.setWindowIcon(QIcon(constant.icon_path))
            msg.exec()
            return False
        if num_on_present and num_off_present:
            msg = (QMessageBox(self.edit_window
                                if hasattr(self, "edit_window")
                                else None))
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Shortcut Conflict")
            msg.setText("You cannot use both 'NumLock ON' and 'NumLock OFF' at the same time. "
                        "Please use only one of of them. If you need both, just use 'Caps Lock'.")
            msg.setWindowIcon(QIcon(constant.icon_path))
            msg.exec()
            return False
        return True

    def get_program_condition(self):
        "Get program binding value from entry"
        program_entry = self.program_entry.text().strip()
        program_condition = ""

        if program_entry:
            pattern = r"\[(Tittle|Class|Process),\s*([^\]]+)\]"
            matches = re.findall(pattern, program_entry)
            conditions = []
            for typ, value in matches:
                value = value.strip()
                if typ.lower() == "process":
                    conditions.append(f'WinActive("ahk_exe {value}")')
                elif typ.lower() == "class":
                    conditions.append(f'WinActive("ahk_class {value}")')
                elif typ.lower() == "tittle":
                    conditions.append(f'WinActive("{value}")')
            program_condition = " || ".join(conditions)

        return program_condition

    def get_device_condition(self):
        "Get device binding value from entry"
        device_condition = ""
        device_name = self.keyboard_entry.text().strip()
        if device_name:
            device_condition = "cm1.IsActive"
        return device_condition

    def write_condition(self, file, write_shortcuts=False,
                        write_program=False, write_device=False):
        "Write Hotif condition for shortcuts, device, program in one hotif line"
        program = self.get_program_condition() if write_program else None

        hotif_conditions = []

        # Shortcuts condition
        self.shortcuts_condition(file, hotif_conditions, write_shortcuts)

        # Device condition
        self.device_condition(file, hotif_conditions, write_device)

        if program:
            hotif_conditions.append(f"({program})")

        if hotif_conditions:
            file.write("SetTitleMatchMode 2\n")
            file.write(f"#HotIf {' && '.join(hotif_conditions)}\n")
            return True
        return False

    def device_condition(self, file, hotif_conditions, write_device):
        "Device condition"
        device = self.keyboard_entry.text().strip() if write_device else None
        if device:
            parts = device.split(",", 1)
            device_type = parts[0].strip().lower()
            vid_pid_or_handle = parts[1].strip() if len(parts) > 1 else ""
            if device_type == "mouse":
                is_mouse = True
            elif device_type == "keyboard":
                is_mouse = False
            else:
                raise ValueError(f"Unknown device type: {device_type}")
            file.write("Persistent\n")
            file.write("#include AutoHotkey Interception\\Lib\\AutoHotInterception.ahk\n\n")
            file.write("AHI := AutoHotInterception()\n")
            file.write(
                (
                f'id1 := AHI.GetDeviceIdFromHandle({str(is_mouse).lower()}, '
                f'"{vid_pid_or_handle}")\n'
                )
            )
            file.write("cm1 := AHI.CreateContextManager(id1)\n\n")
            hotif_conditions.append("cm1.IsActive")

    def shortcuts_condition(self, file, hotif_conditions, write_shortcuts=False):
        "Shortcuts condition"
        shortcuts = None
        if write_shortcuts:
            shortcuts = [
                shortcut_row[0].text().strip()
                for shortcut_row in self.shortcut_rows
                if self.write_script.is_widget_valid(shortcut_row)
                and shortcut_row[0].text().strip()
            ] or None

        if shortcuts:
            valid_shortcuts = [s for s in shortcuts if s]
            if valid_shortcuts:
                caps_shortcuts = []
                normal_shortcuts = []
                for shortcut in valid_shortcuts:
                    if shortcut.lower() == "capslock on":
                        caps_shortcuts.append('GetKeyState("CapsLock", "T")')
                    elif shortcut.lower() == "capslock off":
                        caps_shortcuts.append('!GetKeyState("CapsLock", "T")')
                    elif shortcut.lower() == "numlock on":
                        caps_shortcuts.append('GetKeyState("NumLock", "T")')
                    elif shortcut.lower() == "numlock off":
                        caps_shortcuts.append('!GetKeyState("NumLock", "T")')
                    else:
                        normal_shortcuts.append(shortcut)
                if normal_shortcuts:
                    file.write("toggle := false\n\n")
                    for shortcut in normal_shortcuts:
                        translated_shortcut = self.write_script.translate_key(shortcut)
                        file.write(f"~{translated_shortcut}:: ; Shortcuts\n")
                        file.write("{\n    global toggle\n    toggle := !toggle\n}\n\n")
                    hotif_conditions.append("toggle")
                elif caps_shortcuts:
                    hotif_conditions.append(" || ".join(caps_shortcuts))
