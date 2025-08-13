import os
from PySide6.QtWidgets import (
    QWidget, QDialog, QLabel, QLineEdit, QPushButton, QTextEdit, QScrollArea,
    QVBoxLayout, QSpacerItem, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.utility.constant import (icon_path)

class EditScriptMain:
    def edit_script(self, script_name):
        # Always clear row widget tracking lists to avoid stale/deleted widget references
        self.shortcut_row_widgets = []
        self.mapping_row_widgets = []
        self.copas_rows = []

        self.is_text_mode = False  # Initialize is_text_mode to False

        # New profile mode if script_name is None or empty
        is_new_profile = not script_name
        if is_new_profile:
            script_path = None
            lines = ["; default\n"]  # Ensure at least one line for new profile
        else:
            script_path = os.path.join(self.SCRIPT_DIR, script_name)
            # Read the existing script content
            with open(script_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                first_line = file.readline().strip()
            if not lines:
                return

        first_line = lines[0].strip()
        key_map = self.load_key_list()
        mode_line = lines[0].strip() if lines else "; default"

        # Create a new window for editing the script
        self.edit_window = QDialog(self)
        if is_new_profile:
            self.edit_window.setWindowTitle("Create New Profile")
        else:
            self.edit_window.setWindowTitle("Edit Profile")
        self.edit_window.setWindowIcon(QIcon(icon_path))
        self.edit_window.setFixedSize(600, 450)
        # No direct equivalent for .transient, but parent is set

        # Input for script name
        script_name_label = QLabel("Profile Name    :", self.edit_window)
        script_name_label.move(int(0.13 * 600), int(0.006 * 450))
        script_name_entry = QLineEdit(self.edit_window)
        if script_name:
            script_name_without_extension = script_name.replace('.ahk', '')
            script_name_entry.setText("    " + script_name_without_extension)
            script_name_entry.setReadOnly(True)
        else:
            script_name_entry.setText("")
            script_name_entry.setReadOnly(False)
        script_name_entry.move(int(0.31 * 600), int(0.01 * 450))
        script_name_entry.resize(int(0.557 * 600), 22)
        self.script_name_entry = script_name_entry

        program_label = QLabel("Program           :", self.edit_window)
        program_label.move(int(0.13 * 600), int(0.066 * 450))
        program_entry = QLineEdit(self.edit_window)
        program_entry.move(int(0.31 * 600), int(0.07 * 450))
        program_entry.resize(int(0.38 * 600), 22)
        program_select_button = QPushButton("Select Program", self.edit_window)
        program_select_button.move(int(0.71 * 600), int(0.06 * 450))
        program_select_button.resize(95, 22)
        program_select_button.clicked.connect(lambda: self.edit_open_select_program_window(self.program_entry))
        self.program_entry = program_entry

        keyboard_label = QLabel("Device ID           :", self.edit_window)
        keyboard_label.move(int(0.13 * 600), int(0.126 * 450))
        keyboard_entry = QLineEdit(self.edit_window)
        keyboard_entry.move(int(0.31 * 600), int(0.13 * 450))
        keyboard_entry.resize(int(0.38 * 600), 22)
        keyboard_select_button = QPushButton("Select Device", self.edit_window)
        keyboard_select_button.move(int(0.71 * 600), int(0.12 * 450))
        keyboard_select_button.resize(95, 22)
        keyboard_select_button.clicked.connect(self.edit_open_device_selection)
        self.keyboard_entry = keyboard_entry

        # Device parsing
        device_id = self.parse_device(lines)
        if device_id:
            keyboard_entry.setText("    " + device_id)

        # Program parsing
        program_entry_value = self.parse_program(lines)
        if program_entry_value:
            program_entry.setText("    " + program_entry_value)

        # Scrollable area for key mappings
        self.edit_scroll = QScrollArea(self.edit_window)
        self.edit_scroll.setGeometry(int(0.067 * 600), int(0.178 * 450), int(0.875 * 600), int(0.678 * 450))
        self.edit_scroll.setWidgetResizable(True)
        # Always show vertical scrollbar
        self.edit_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # Optionally, always show horizontal scrollbar too:
        # self.edit_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.edit_frame = QWidget()
        self.edit_scroll.setWidget(self.edit_frame)
        self.edit_frame_layout = QVBoxLayout(self.edit_frame)
        self.edit_frame.setLayout(self.edit_frame_layout)

        # Scrollable area for key mappings
        self.edit_scroll = QScrollArea(self.edit_window)
        self.edit_scroll.setGeometry(int(0.067 * 600), int(0.178 * 450), int(0.875 * 600), int(0.678 * 450))
        self.edit_scroll.setWidgetResizable(True)
        # Always show vertical scrollbar
        self.edit_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # Optionally, always show horizontal scrollbar too:
        # self.edit_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.edit_frame = QWidget()
        self.edit_scroll.setWidget(self.edit_frame)
        self.edit_frame_layout = QVBoxLayout(self.edit_frame)
        self.edit_frame.setLayout(self.edit_frame_layout)

        # Initialize key_rows and shortcut_rows based on mode
        self.key_rows = []
        self.shortcut_rows = []

        shortcuts = []
        remaps = []

        # Parsing remaps and shortcuts
        if mode_line == "; default":
            shortcuts, remaps = self.parse_default(lines, key_map)
        elif mode_line == "; text":
            self.is_text_mode = True
            self.text_block = QTextEdit(self.edit_frame)
            self.text_block.setLineWrapMode(QTextEdit.WidgetWidth)
            self.text_block.setFixedHeight(14 * self.fontMetrics().height())
            self.text_block.setFontPointSize(10)
            self.edit_frame_layout.addWidget(self.text_block)

            shortcuts = self.parse_shortcuts(lines, key_map)

            self.row_num += 1

            text_content = self.extract_and_filter_content(lines)
            self.text_block.setPlainText(text_content.strip())

        # Only add shortcut/mapping rows for default/text modes
        if mode_line == "; default":
            if not shortcuts:
                self.add_edit_shortcut_mapping_row()
            else:
                for shortcut in shortcuts:
                    self.add_edit_shortcut_mapping_row(shortcut)
            if not remaps:
                self.add_edit_mapping_row()
            else:
                for original_key, remap_key, is_text_format, is_hold_format, hold_interval in remaps:
                    self.add_edit_mapping_row(original_key, remap_key)
                    # Set the text format checkbox state for the last added row
                    if self.key_rows and len(self.key_rows[-1]) == 7:  # Changed from 5 to 7 to account for hold_format_var and hold_interval_entry
                        _, _, _, _, text_format_var, hold_format_var, hold_interval_entry = self.key_rows[-1]
                        text_format_var.setChecked(is_text_format)
                        hold_format_var.setChecked(is_hold_format)
                        if is_hold_format and hold_interval:
                            hold_interval_entry.clear()
                            # Convert string to float first, then format as integer if whole number
                            hold_interval_float = float(hold_interval)
                            hold_interval_str = str(int(hold_interval_float)) if hold_interval_float.is_integer() else str(hold_interval_float)
                            hold_interval_entry.setText(hold_interval_str)
                            
        elif mode_line == "; text":
            if not shortcuts:
                self.add_edit_shortcut_mapping_row()
            else:
                for shortcut in shortcuts:
                    self.add_edit_shortcut_mapping_row(shortcut)

        elif mode_line == "; multi copy":
            if not shortcuts:
                self.add_edit_shortcut_mapping_row()
            else:
                for shortcut in shortcuts:
                    self.add_edit_shortcut_mapping_row(shortcut)

        self.edit_frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        save_button = QPushButton("Save Changes", self.edit_window)
        save_button.move(int(0.070 * 600), int(0.889 * 450))
        save_button.resize(107, 26)
        save_button.clicked.connect(lambda: self.save_changes(script_name))

        mode_combobox = QComboBox(self.edit_window)
        mode_combobox.addItems([
            "Default Mode",
            "Text Mode",
        ])
        mode_combobox.move(450, 400)
        mode_combobox.setEditable(True)
        mode_combobox.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_combobox.lineEdit().setReadOnly(True)
        mode_combobox.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.mode_combobox = mode_combobox  # <-- Add this line

        # Set default index based on first_line
        first_line_lower = first_line.lower()
        mode_map = {
            "; default": 0,
            "; text": 1,
        }
        default_index = mode_map.get(first_line_lower, 0)
        mode_combobox.setCurrentIndex(default_index)

        # --- Add combobox handler ---
        on_mode_changed = self.handle_mode_changed
        mode_combobox.currentIndexChanged.connect(on_mode_changed)

        # Update the scrollable region of the canvas
        self.update_scroll_region()

        # Show the dialog modally
        self.edit_window.exec()  # <-- Add this line to display the dialog modally

    def handle_mode_changed(self, index):
        # Clear the edit_frame_layout
        while self.edit_frame_layout.count():
            item = self.edit_frame_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        # Reset row tracking
        self.key_rows = []
        self.shortcut_rows = []
        if hasattr(self, "files_opener_rows"):
            self.files_opener_rows = []
        if hasattr(self, "files_opener_row_widgets"):
            self.files_opener_row_widgets = []
        if hasattr(self, "text_block"):
            self.text_block = None
        self.is_text_mode = False

        # Call the appropriate function for the selected mode
        if index == 0:  # Default Mode
            self.is_text_mode = False
            self.add_edit_shortcut_mapping_row()
            self.add_edit_mapping_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        elif index == 1:  # Text Mode
            self.is_text_mode = True
            self.add_edit_shortcut_mapping_row()
            self.edit_frame_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.update_scroll_region()

    def update_scroll_region(self):
        if hasattr(self, "edit_frame") and self.edit_frame is not None:
            self.edit_frame.adjustSize()
            if hasattr(self, "edit_scroll") and self.edit_scroll is not None:
                self.edit_scroll.widget().update()