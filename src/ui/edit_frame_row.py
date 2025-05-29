from PySide6.QtWidgets import (
    QLabel, QPushButton, QCheckBox, QLineEdit, QFrame, QComboBox, QHBoxLayout,
    QVBoxLayout, QWidget, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt

class edit_frame_row:
    def add_edit_mapping_row(self, original_key='', remap_key=''):
        # Ensure edit_frame has a layout
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        # Container widget for this mapping row
        row_widget = QWidget(self.edit_frame)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # Prevent vertical stretching
        row_layout = QGridLayout(row_widget)
        row_widget.setLayout(row_layout)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setHorizontalSpacing(10)
        row_layout.setVerticalSpacing(5)

        # Default Key label
        select_default_key_label = QLabel("Default Key:", row_widget)
        select_default_key_label.setFixedWidth(80)
        row_layout.addWidget(select_default_key_label, 0, 0, 2, 1)

        # Select Default Key button
        original_key_select = QPushButton("Select Default Key", row_widget)
        original_key_select.setFixedWidth(120)
        original_key_select.clicked.connect(lambda: self.toggle_shortcut_key_listening(original_key_entry, original_key_select))
        row_layout.addWidget(original_key_select, 0, 1)

        # Remap Key label
        select_remap_key_label = QLabel("Remap Key:", row_widget)
        select_remap_key_label.setFixedWidth(80)
        row_layout.addWidget(select_remap_key_label, 0, 2, 2, 1)

        # Select Remap Key button
        remap_key_select = QPushButton("Select Remap Key", row_widget)
        remap_key_select.setFixedWidth(120)
        remap_key_select.clicked.connect(lambda: self.toggle_shortcut_key_listening(remap_key_entry, remap_key_select))
        row_layout.addWidget(remap_key_select, 0, 3)

        # Comboboxes for key entries
        key_values = self.load_key_values()

        original_key_entry = QComboBox(row_widget)
        original_key_entry.setEditable(True)
        original_key_entry.addItems(key_values)
        if original_key:
            original_key_entry.setCurrentText(original_key)
        original_key_entry.setFixedWidth(120)
        row_layout.addWidget(original_key_entry, 1, 1)

        remap_key_entry = QComboBox(row_widget)
        remap_key_entry.setEditable(True)
        remap_key_entry.addItems(key_values)
        if remap_key:
            remap_key_entry.setCurrentText(remap_key)
        remap_key_entry.setFixedWidth(120)
        row_layout.addWidget(remap_key_entry, 1, 3)

        # Format label and checkboxes row
        format_label = QLabel("Remap Format:", row_widget)
        format_label.setFixedWidth(80)
        row_layout.addWidget(format_label, 2, 0)

        text_format_checkbox = QCheckBox("Text Format", row_widget)
        row_layout.addWidget(text_format_checkbox, 2, 1)

        hold_format_checkbox = QCheckBox("Hold Format", row_widget)
        row_layout.addWidget(hold_format_checkbox, 2, 2)

        hold_interval_entry = QLineEdit(row_widget)
        hold_interval_entry.setPlaceholderText("Hold Interval")
        hold_interval_entry.setFixedWidth(120)
        hold_interval_entry.setStyleSheet("color: lightgray;")
        row_layout.addWidget(hold_interval_entry, 2, 3)

        # Save references for later use
        self.key_rows.append((original_key_entry, remap_key_entry, original_key_select, remap_key_select, text_format_checkbox, hold_format_checkbox, hold_interval_entry))

        # Separator with plus button
        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(20, 0, 20, 0)
        separator_layout.setSpacing(5)

        left_sep = QFrame(separator_widget)
        left_sep.setFrameShape(QFrame.Shape.HLine)
        left_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(left_sep)

        plus_label = QLabel("+", separator_widget)
        plus_label.setStyleSheet("""
            color: gray;
            padding: 0 5px;
            font-size: 14px;
            font-weight: bold;
        """)
        plus_label.setCursor(Qt.CursorShape.PointingHandCursor)
        plus_label.setFixedWidth(20)  # Increased width to accommodate larger text
        plus_label.setFixedHeight(20)  # Set fixed height to match width
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the text
        separator_layout.addWidget(plus_label)
        def on_plus_click(event):
            self.add_edit_mapping_row()
        plus_label.mousePressEvent = on_plus_click

        right_sep = QFrame(separator_widget)
        right_sep.setFrameShape(QFrame.Shape.HLine)
        right_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(right_sep)

        # Add row and separator to the main layout
        self.edit_frame_layout.addWidget(row_widget)
        self.edit_frame_layout.addWidget(separator_widget)

    def add_edit_shortcut_mapping_row(self, shortcut=''):
        # Ensure edit_frame has a layout
        if not hasattr(self.edit_frame, 'layout'):
            self.edit_frame_layout = QVBoxLayout(self.edit_frame)
            self.edit_frame.setLayout(self.edit_frame_layout)
        else:
            self.edit_frame_layout = self.edit_frame.layout()

        # If in text mode and text_block doesn't exist, create it (migrated logic)
        if self.is_text_mode and (not hasattr(self, 'text_block') or self.text_block is None):
            from PySide6.QtWidgets import QTextEdit
            self.text_block = QTextEdit(self.edit_frame)
            self.text_block.setReadOnly(False)
            self.text_block.setFixedHeight(14 * 20)  # Approximate height for 14 lines
            self.text_block.setFixedWidth(70 * 8)    # Approximate width for 70 chars
            self.text_block.setStyleSheet("font-family: Consolas; font-size: 10pt;")
            self.edit_frame_layout.addWidget(self.text_block)

        # Container widget for this shortcut row
        row_widget = QWidget(self.edit_frame)
        row_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)  # Prevent vertical stretching
        row_layout = QGridLayout(row_widget)
        row_widget.setLayout(row_layout)
        row_layout.setContentsMargins(10, 5, 10, 5)
        row_layout.setHorizontalSpacing(10)
        row_layout.setVerticalSpacing(5)

        # Shortcut Key label
        shortcut_label = QLabel("Shortcut Key:", row_widget)
        shortcut_label.setFixedWidth(80)
        row_layout.addWidget(shortcut_label, 0, 0)

        # Shortcut Key select button
        shortcut_key_select = QPushButton("Select Shortcut Key", row_widget)
        shortcut_key_select.setFixedWidth(280)
        shortcut_key_select.clicked.connect(lambda: self.toggle_shortcut_key_listening(shortcut_entry, shortcut_key_select))
        row_layout.addWidget(shortcut_key_select, 0, 1, 1, 2)

        # Combobox for shortcut entry
        key_values = self.load_key_values()
        shortcut_entry = QComboBox(row_widget)
        shortcut_entry.setEditable(True)
        shortcut_entry.addItems(key_values)
        if shortcut:
            shortcut_entry.setCurrentText(shortcut)
        shortcut_entry.setFixedWidth(280)
        row_layout.addWidget(shortcut_entry, 1, 1, 1, 2)
        self.shortcut_entry = shortcut_entry

        # Save reference for later
        self.shortcut_rows.append((shortcut_entry, shortcut_key_select))

        # Separator with plus button
        separator_widget = QWidget(self.edit_frame)
        separator_layout = QHBoxLayout(separator_widget)
        separator_widget.setLayout(separator_layout)
        separator_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        separator_layout.setContentsMargins(20, 0, 20, 0)
        separator_layout.setSpacing(5)

        left_sep = QFrame(separator_widget)
        left_sep.setFrameShape(QFrame.Shape.HLine)
        left_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(left_sep)

        # Only add + button if not a special script
        script_name = self.script_name_entry.text().strip().lower() if hasattr(self, 'script_name_entry') else ""
        
        plus_label = QLabel("+", separator_widget)
        plus_label.setStyleSheet("""
            color: gray;
            padding: 0 5px;
            font-size: 14px;
            font-weight: bold;
        """)
        plus_label.setCursor(Qt.CursorShape.PointingHandCursor)
        plus_label.setFixedWidth(20)  # Increased width to accommodate larger text
        plus_label.setFixedHeight(20)  # Set fixed height to match width
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the text
        separator_layout.addWidget(plus_label)
        def on_plus_click(event):
            self.add_edit_shortcut_mapping_row()
        plus_label.mousePressEvent = on_plus_click
        
        right_sep = QFrame(separator_widget)
        right_sep.setFrameShape(QFrame.Shape.HLine)
        right_sep.setFrameShadow(QFrame.Shadow.Sunken)
        separator_layout.addWidget(right_sep)

        # Add row and separator to the main layout
        self.edit_frame_layout.addWidget(row_widget)
        self.edit_frame_layout.addWidget(separator_widget)

        # If in Text Mode, re-add the text block below the shortcut rows
        if self.is_text_mode and hasattr(self, 'text_block') and self.text_block is not None:
            self.edit_frame_layout.addWidget(self.text_block)